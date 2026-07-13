"""
=============================================================================
Stage 3: LLM Inference & Context Orchestration (Core RAG Logic)
=============================================================================

PURPOSE
-------
Implements the retrieval-augmented generation loop: given a user question,
find relevant document chunks, assemble context, generate a grounded answer,
and enforce anti-hallucination guardrails.

ROLE IN THE RAG PIPELINE
------------------------
  This is the BRAIN of the system — called by:
    - evaluate.py (Stage 4 benchmarking)
    - api/app.py (Stage 5 live /query endpoint)

  Dependencies:
    - embed.VectorIndex (ChromaDB retrieval)
    - text_preprocessor.TextPreprocessor (query normalization)
    - settings.yaml (retrieval, LLM, guardrails config)

QUERY FLOW (RAGPipeline.query):
  1. RETRIEVE  — embed query → ChromaDB top_k → optional cross-encoder rerank
  2. FILTER    — drop chunks below similarity_threshold
  3. CONTEXT   — assemble labeled chunks up to max_context_tokens
  4. GENERATE  — Ollama/Gemini/extractive fallback
  5. GUARDRAILS — abstain if no context; cite sources; compute confidence

PIPELINE MODES (benchmarked in evaluate.py):
  local_llm      — bi-encoder retrieval + Ollama LLM
  reranked_local — cross-encoder rerank + Ollama LLM  ← RECOMMENDED
  extractive     — retrieval-only baseline (no LLM generation)
  api_llm        — cloud Gemini (optional, needs GEMINI_API_KEY)
  reranked_gemini — cross-encoder + Gemini

INTERVIEW TALKING POINTS
------------------------
1. **Two-stage retrieval:** Bi-encoder (fast, broad recall) → cross-encoder
   (slow, high precision) is the standard enterprise RAG pattern for policy Q&A.
2. **Query preprocessing only:** Documents keep full vocabulary in the index;
   stop-word removal + lemmatization on queries improves embedding match quality.
3. **Context-only system prompt:** LLM instructed to answer ONLY from context;
   abstain phrase is exact-match enforced — reduces fabrication risk.
4. **Ollama fallback chain:** /api/chat → /api/generate → keyword extractive
   fallback if Ollama offline — graceful degradation for demos.
5. **Confidence from retrieval:** Not LLM self-report — derived from chunk
   similarity scores (avg + max blend). More trustworthy for enterprise UI.
6. **save_pipeline_state():** Persists active mode + config snapshot for API bootstrap.
"""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder, SentenceTransformer

from src.embed import RetrievedChunk, VectorIndex
from src.text_preprocessor import TextPreprocessor
from src.utils import load_config, resolve_path, save_json, setup_logging

load_dotenv()
logger = setup_logging("orchestrate")

# Available pipeline modes — Literal enables type checking at call sites
PipelineMode = Literal["local_llm", "api_llm", "reranked_gemini", "reranked_local", "extractive"]

# -----------------------------------------------------------------------------
# System prompt — context injection template for the LLM
# -----------------------------------------------------------------------------
# Interview: {context} and {query} are filled at runtime; {abstain_phrase} from config.
# Rules 1-5 enforce grounded, cited, concise enterprise answers.
SYSTEM_PROMPT = """You are an enterprise knowledge assistant. Answer ONLY using the provided context.

Rules:
1. Base every claim on the context below. Do not invent policies, numbers, or procedures.
2. If the context is insufficient, respond exactly with: "{abstain_phrase}"
3. Cite source filenames in parentheses when stating specific facts.
4. Be concise and operational. Prefer bullet points for multi-step procedures.
5. Never speculate about information not present in the context.

Context:
{context}

Question: {query}

Answer:"""


# -----------------------------------------------------------------------------
# Response data models
# -----------------------------------------------------------------------------
@dataclass
class SourceMetadata:
    """Citation bundle for one retrieved chunk — returned in API responses."""
    source_file: str
    doc_type: str
    section_hint: str
    similarity: float
    distance: float
    excerpt: str  # first 240 chars — UI preview without full chunk text


@dataclass
class QueryResult:
    """Complete RAG output for one user question."""
    answer: str
    confidence: float
    sources: list[SourceMetadata]
    pipeline: str
    latency_ms: float
    retrieval_scores: list[float]


# -----------------------------------------------------------------------------
# RAGPipeline — main orchestrator class
# -----------------------------------------------------------------------------
class RAGPipeline:
    """
    Wires retrieval, reranking, context assembly, and LLM generation together.

    Instantiate once at API startup (singleton); reuse for every /query request.
    Models loaded in __init__: SentenceTransformer, VectorIndex, optional CrossEncoder.
    """

    def __init__(self, mode: PipelineMode = "reranked_local"):
        """
        Initialize pipeline with config-driven models and guardrails.

        Cross-encoder reranker loaded only for modes containing "reranked" —
        saves ~100MB RAM and load time for local_llm/extractive modes.
        """
        self.config = load_config()
        self.mode = mode
        self.retrieval_cfg = self.config["retrieval"]
        self.llm_cfg = self.config["llm"]
        self.guardrails = self.config["anti_hallucination"]

        # Same embedding model as Stage 2 — critical for retrieval consistency
        embed_model = self.config["embedding"]["model_name"]
        self.embedder = SentenceTransformer(embed_model)
        self.index = VectorIndex(self.config["paths"]["vector_store_dir"])

        # NLTK preprocessor: query-side stop-word removal + lemmatization
        pre_cfg = self.config.get("preprocessing", {})
        self.preprocessor = TextPreprocessor(
            remove_stopwords=pre_cfg.get("remove_stopwords", True),
            lemmatize=pre_cfg.get("lemmatize", True),
            min_token_length=pre_cfg.get("min_token_length", 2),
        )

        # Cross-encoder: ms-marco-MiniLM-L-6-v2 — trained for passage ranking
        self.reranker: CrossEncoder | None = None
        if "reranked" in mode:
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    # -------------------------------------------------------------------------
    # Step 1+2: Retrieval (+ optional cross-encoder reranking)
    # -------------------------------------------------------------------------
    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        """
        Vector search with optional cross-encoder reranking and threshold filter.

        Flow:
          1. Preprocess query (NLTK) → embed → ChromaDB top_k candidates
          2. If reranker: score (query, chunk) pairs → keep rerank_top_k
          3. Else: truncate to rerank_top_k by vector similarity order
          4. Filter chunks below similarity_threshold
        """
        processed_query = self.preprocessor.preprocess(query) or query
        query_emb = self.embedder.encode(processed_query, normalize_embeddings=True).tolist()
        candidates = self.index.query(query_emb, top_k=self.retrieval_cfg["top_k"])

        if self.reranker is not None:
            pairs = [[processed_query, c.text] for c in candidates]
            scores = self.reranker.predict(pairs)
            ranked = sorted(
                zip(candidates, scores),
                key=lambda item: float(item[1]),
                reverse=True,
            )
            candidates = [item[0] for item in ranked[: self.retrieval_cfg["rerank_top_k"]]]
        else:
            candidates = candidates[: self.retrieval_cfg["rerank_top_k"]]

        threshold = self.retrieval_cfg["similarity_threshold"]
        return [c for c in candidates if c.similarity >= threshold]

    # -------------------------------------------------------------------------
    # Step 3: Context assembly for LLM prompt
    # -------------------------------------------------------------------------
    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        """
        Assemble retrieved chunks into a labeled context string.

        Each block includes source metadata header for LLM citation.
        Stops adding chunks when max_context_tokens (word-count approx) exceeded.
        """
        parts: list[str] = []
        total_tokens = 0
        max_tokens = self.guardrails["max_context_tokens"]
        for chunk in chunks:
            block = (
                f"[Source: {chunk.source_file} | Type: {chunk.doc_type} | "
                f"Section: {chunk.section_hint} | Similarity: {chunk.similarity:.3f}]\n"
                f"{chunk.text}"
            )
            approx_tokens = len(block.split())
            if total_tokens + approx_tokens > max_tokens:
                break
            parts.append(block)
            total_tokens += approx_tokens
        return "\n\n---\n\n".join(parts)

    # -------------------------------------------------------------------------
    # Confidence estimation (retrieval-based, not LLM self-report)
    # -------------------------------------------------------------------------
    def _compute_confidence(self, chunks: list[RetrievedChunk], answer: str) -> float:
        """
        Estimate answer confidence from retrieval similarity scores.

        Formula: 0.5 * avg_similarity + 0.5 * max_similarity, capped at 0.99.
        Abstention answers → 0.1; no chunks → 0.0.
        """
        if not chunks:
            return 0.0
        abstain = self.guardrails["abstain_phrase"].lower()
        if abstain in answer.lower():
            return 0.1
        avg_sim = sum(c.similarity for c in chunks) / len(chunks)
        top_sim = max(c.similarity for c in chunks)
        return round(min(0.99, 0.5 * avg_sim + 0.5 * top_sim), 2)

    # -------------------------------------------------------------------------
    # LLM backends — Gemini (cloud), Ollama (local), extractive fallback
    # -------------------------------------------------------------------------
    def _generate_gemini(self, prompt: str) -> str:
        """Call Google Gemini API — requires GEMINI_API_KEY in .env."""
        import google.generativeai as genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Copy .env.example to .env and add your key."
            )
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.llm_cfg["gemini_model"])
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": self.llm_cfg["temperature"],
                "max_output_tokens": self.llm_cfg["max_output_tokens"],
            },
        )
        return (response.text or "").strip()

    def _generate_ollama(self, prompt: str, user_query: str) -> str:
        """
        Call local Ollama LLM — default production path (no API key, data on-prem).

        Tries /api/chat first (messages format), falls back to /api/generate.
        On HTTP error → _fallback_answer (keyword-based extractive response).
        """
        base = self.llm_cfg["ollama_base_url"].rstrip("/")
        timeout = float(self.llm_cfg.get("ollama_timeout_seconds", 120))
        options = {
            "temperature": self.llm_cfg["temperature"],
            "num_predict": self.llm_cfg.get("max_output_tokens", 512),
        }
        chat_payload = {
            "model": self.llm_cfg["ollama_model"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": options,
        }
        generate_payload = {
            "model": self.llm_cfg["ollama_model"],
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        try:
            with httpx.Client(timeout=timeout) as client:
                for url, payload in (
                    (f"{base}/api/chat", chat_payload),
                    (f"{base}/api/generate", generate_payload),
                ):
                    response = client.post(url, json=payload)
                    if response.status_code >= 400:
                        continue
                    data = response.json()
                    if url.endswith("/api/chat"):
                        answer = (data.get("message") or {}).get("content", "").strip()
                    else:
                        answer = data.get("response", "").strip()
                    if answer:
                        return answer
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Ollama unavailable (%s). Using retrieval-only fallback.", exc)
        return self._fallback_answer(user_query, prompt)

    def _fallback_answer(self, query: str, prompt: str) -> str:
        """
        Deterministic extractive fallback when LLM is unavailable.

        Keyword-overlap scoring between query terms and context lines;
        returns top-3 matching lines or first-4-line summary.
        """
        context_start = prompt.find("Context:")
        context_end = prompt.find("Question:")
        if context_start == -1 or context_end == -1:
            return self.guardrails["abstain_phrase"]
        context = prompt[context_start:context_end]
        lines = [
            line.strip()
            for line in context.splitlines()
            if line.strip() and not line.startswith("[Source")
        ]
        if not lines:
            return self.guardrails["abstain_phrase"]

        query_terms = self.preprocessor.extract_keywords(query)
        scored: list[tuple[int, str]] = []
        for line in lines:
            line_terms = self.preprocessor.extract_keywords(line)
            score = len(query_terms & line_terms)
            if score:
                scored.append((score, line))
        if scored:
            best = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
            return " ".join(item[1] for item in best)

        summary = " ".join(lines[:4])
        return f"Based on retrieved documents: {summary[:800]}"

    def _generate(self, prompt: str, user_query: str) -> str:
        """Route to extractive, Gemini, or Ollama based on pipeline mode and config."""
        if self.mode == "extractive":
            return self._fallback_answer(user_query, prompt)

        provider = self.llm_cfg.get("provider", "ollama").lower()
        if provider == "gemini" and self.mode in {"api_llm", "reranked_gemini"}:
            try:
                return self._generate_gemini(prompt)
            except Exception as exc:
                logger.warning("Gemini failed (%s). Falling back to Ollama.", exc)
        return self._generate_ollama(prompt, user_query)

    # -------------------------------------------------------------------------
    # Main entry point — full RAG query
    # -------------------------------------------------------------------------
    def query(self, user_query: str) -> QueryResult:
        """
        Execute the complete RAG pipeline for one natural-language question.

        Early exit: if no chunks pass similarity threshold → abstain immediately
        (no LLM call — saves latency and prevents hallucination on empty context).
        """
        start = time.perf_counter()
        chunks = self._retrieve(user_query)

        if not chunks:
            latency = (time.perf_counter() - start) * 1000
            return QueryResult(
                answer=self.guardrails["abstain_phrase"],
                confidence=0.05,
                sources=[],
                pipeline=self.mode,
                latency_ms=round(latency, 1),
                retrieval_scores=[],
            )

        context = self._build_context(chunks)
        prompt = SYSTEM_PROMPT.format(
            context=context,
            query=user_query,
            abstain_phrase=self.guardrails["abstain_phrase"],
        )
        answer = self._generate(prompt, user_query)
        latency = (time.perf_counter() - start) * 1000

        sources = [
            SourceMetadata(
                source_file=c.source_file,
                doc_type=c.doc_type,
                section_hint=c.section_hint,
                similarity=round(c.similarity, 4),
                distance=round(c.distance, 4),
                excerpt=c.text[:240] + ("..." if len(c.text) > 240 else ""),
            )
            for c in chunks
        ]

        return QueryResult(
            answer=answer,
            confidence=self._compute_confidence(chunks, answer),
            sources=sources,
            pipeline=self.mode,
            latency_ms=round(latency, 1),
            retrieval_scores=[round(c.similarity, 4) for c in chunks],
        )


# -----------------------------------------------------------------------------
# State persistence & serialization helpers
# -----------------------------------------------------------------------------
def save_pipeline_state(mode: PipelineMode) -> None:
    """
    Persist active pipeline config to models/state/pipeline_state.json.

    api/app.py reads this on startup to select ACTIVE_MODE.
    Includes system prompt template and key config snapshots for auditability.
    """
    config = load_config()
    state = {
        "active_pipeline": mode,
        "system_prompt_template": SYSTEM_PROMPT,
        "llm_config": config["llm"],
        "retrieval_config": config["retrieval"],
        "anti_hallucination": config["anti_hallucination"],
    }
    path = resolve_path(config["paths"]["state_dir"]) / "pipeline_state.json"
    save_json(path, state)
    logger.info("Saved pipeline state to %s", path)


def result_to_dict(result: QueryResult) -> dict[str, Any]:
    """Convert QueryResult dataclass to plain dict for FastAPI JSON serialization."""
    payload = asdict(result)
    payload["sources"] = [asdict(s) for s in result.sources]
    return payload
