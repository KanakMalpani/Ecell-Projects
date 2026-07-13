"""
=============================================================================
Stage 2: Embedding Generation & Vector Indexing
=============================================================================

PURPOSE
-------
Transforms text chunks (from Stage 1) into dense vector embeddings and persists
them in a local ChromaDB index for fast approximate nearest-neighbor search.

ROLE IN THE RAG PIPELINE
------------------------
  Input:  data/processed/chunks.json
  Output: models/vector_store/  (ChromaDB HNSW index, cosine space)
          models/state/index_state.json

  At query time (Stage 3 orchestrate.py):
    user question → same embedding model → query vector → ChromaDB.query()
    → top_k RetrievedChunk objects with similarity scores

INTERVIEW TALKING POINTS
------------------------
1. **Bi-encoder retrieval:** Query and documents encoded independently (fast);
   cross-encoder reranking happens later in orchestrate.py (slow but precise).
2. **normalize_embeddings=True:** L2-normalized vectors → cosine similarity =
   dot product; ChromaDB configured with hnsw:space=cosine.
3. **PersistentClient:** Index on disk survives restarts — no Redis/Pinecone
   needed for this enterprise POC; trade-off is single-node scale.
4. **Batch encoding:** batch_size=32 amortizes GPU/CPU overhead across chunks.
5. **Metadata stored with vectors:** source_file, doc_type, section_hint enable
   citation in API responses without re-reading original PDFs.
6. **reset vs append:** Default wipe-and-rebuild ensures reproducible demos;
   --no-reset supports incremental indexing in production extensions.

FLOW:
  1. Load chunks.json from Stage 1
  2. Encode each chunk with sentence-transformers (all-MiniLM-L6-v2)
  3. Store vectors + metadata in ChromaDB (models/vector_store/)
  4. Save index_state.json with stats
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.utils import load_config, load_json, resolve_path, save_json, setup_logging

logger = setup_logging("embed")


# -----------------------------------------------------------------------------
# Data model — one retrieved chunk with similarity metadata
# -----------------------------------------------------------------------------
@dataclass
class RetrievedChunk:
    """
    One chunk returned by vector search, enriched with similarity score.

    Consumed by orchestrate.py when building LLM context and API source citations.

    distance:   ChromaDB cosine distance (0 = identical, 2 = opposite direction)
    similarity: 1 - distance, clamped to >= 0.0 (higher = better match)
    """
    chunk_id: str
    text: str
    source_file: str
    doc_type: str
    section_hint: str
    distance: float
    similarity: float


# -----------------------------------------------------------------------------
# VectorIndex — ChromaDB wrapper for enterprise document collection
# -----------------------------------------------------------------------------
class VectorIndex:
    """
    ChromaDB-backed local vector store for enterprise document chunks.

    Design decisions:
      - PersistentClient: index survives server restarts (disk at vector_store_dir)
      - Collection name "enterprise_docs": single corpus per deployment
      - Cosine space: standard for normalized sentence embeddings

    Interview note: ChromaDB uses HNSW approximate search — O(log n) query time
    with small recall trade-off vs. brute-force; acceptable for <100k chunks.
    """

    def __init__(self, persist_dir: str, collection_name: str = "enterprise_docs"):
        """Open or create the persistent ChromaDB collection."""
        self.persist_dir = resolve_path(persist_dir)
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        """
        Delete and recreate the collection.

        Used when rebuilding the full index (default build_index behavior).
        Interview: full rebuild avoids stale chunk IDs from removed documents.
        """
        name = self.collection.name
        self.client.delete_collection(name)
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: list[dict[str, Any]],
        embeddings: list[list[float]],
    ) -> None:
        """
        Batch-insert chunk texts, precomputed embeddings, and metadata.

        ChromaDB stores three parallel arrays: ids, embeddings, documents, metadatas.
        chunk_id from ingest.py becomes the stable primary key.
        """
        self.collection.add(
            ids=[c["chunk_id"] for c in chunks],
            embeddings=embeddings,
            documents=[c["text"] for c in chunks],
            metadatas=[
                {
                    "source_file": c["source_file"],
                    "doc_type": c["doc_type"],
                    "section_hint": c["section_hint"],
                    "token_count": c["token_count"],
                }
                for c in chunks
            ],
        )

    def query(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        """
        Approximate nearest-neighbor search for the query embedding.

        Returns up to top_k chunks; orchestrate.py may rerank/filter further.
        Results are NOT re-sorted here — ChromaDB returns by distance ascending.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        retrieved: list[RetrievedChunk] = []
        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for idx, doc_id in enumerate(ids):
            distance = float(distances[idx])
            similarity = max(0.0, 1.0 - distance)
            meta = metas[idx]
            retrieved.append(
                RetrievedChunk(
                    chunk_id=doc_id,
                    text=docs[idx],
                    source_file=meta["source_file"],
                    doc_type=meta["doc_type"],
                    section_hint=meta["section_hint"],
                    distance=distance,
                    similarity=similarity,
                )
            )
        return retrieved

    def count(self) -> int:
        """Return total vectors in the collection — used for index_state.json."""
        return self.collection.count()


# -----------------------------------------------------------------------------
# build_index — full Stage 2 pipeline (load → encode → persist → state)
# -----------------------------------------------------------------------------
def build_index(
    processed_dir: str | None = None,
    vector_store_dir: str | None = None,
    reset: bool = True,
) -> dict[str, Any]:
    """
    Full indexing pipeline: load chunks → embed → store in ChromaDB → save state.

    Args:
        processed_dir: override path to chunks.json directory
        vector_store_dir: override ChromaDB persist path
        reset: if True, wipe existing index before inserting (default: full rebuild)

    Returns:
        state dict persisted to models/state/index_state.json

    Raises:
        FileNotFoundError: if chunks.json missing (Stage 1 not run)
    """
    config = load_config()
    processed = resolve_path(processed_dir or config["paths"]["processed_dir"])
    store_dir = vector_store_dir or config["paths"]["vector_store_dir"]
    embed_cfg = config["embedding"]

    chunks_path = processed / "chunks.json"
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Missing {chunks_path}. Run stage 1 first: python scripts/run_ingest.py"
        )

    chunks: list[dict[str, Any]] = load_json(chunks_path)
    logger.info("Loading embedding model: %s", embed_cfg["model_name"])
    model = SentenceTransformer(embed_cfg["model_name"])

    texts = [c["text"] for c in chunks]
    logger.info("Encoding %d chunks...", len(texts))
    embeddings = model.encode(
        texts,
        batch_size=embed_cfg["batch_size"],
        show_progress_bar=True,
        normalize_embeddings=True,  # unit-length vectors for cosine similarity
    ).tolist()

    index = VectorIndex(store_dir)
    if reset:
        index.reset()
    index.add_chunks(chunks, embeddings)

    state = {
        "embedding_model": embed_cfg["model_name"],
        "chunk_count": len(chunks),
        "vector_count": index.count(),
        "distance_metric": "cosine",
        "collection_name": "enterprise_docs",
    }
    state_path = resolve_path(config["paths"]["state_dir"]) / "index_state.json"
    save_json(state_path, state)
    logger.info("Indexed %d vectors at %s", index.count(), store_dir)
    return state


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------
def main() -> None:
    """CLI entry point: python scripts/run_embed.py [--no-reset]"""
    parser = argparse.ArgumentParser(description="Stage 2: embed and index chunks")
    parser.add_argument("--no-reset", action="store_true", help="Append without resetting index")
    args = parser.parse_args()
    build_index(reset=not args.no_reset)


if __name__ == "__main__":
    main()
