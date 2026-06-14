"""Stage 2: Embedding generation and vector indexing."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from src.utils import load_config, load_json, resolve_path, save_json, setup_logging

logger = setup_logging("embed")


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    source_file: str
    doc_type: str
    section_hint: str
    distance: float
    similarity: float


class VectorIndex:
    """ChromaDB-backed local vector store with serialization."""

    def __init__(self, persist_dir: str, collection_name: str = "enterprise_docs"):
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
        return self.collection.count()


def build_index(
    processed_dir: str | None = None,
    vector_store_dir: str | None = None,
    reset: bool = True,
) -> dict[str, Any]:
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
        normalize_embeddings=True,
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2: embed and index chunks")
    parser.add_argument("--no-reset", action="store_true", help="Append without resetting index")
    args = parser.parse_args()
    build_index(reset=not args.no_reset)


if __name__ == "__main__":
    main()
