"""Stage 3: LLM inference and context orchestration."""

from __future__ import annotations

import os
import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from sentence_transformers import CrossEncoder, SentenceTransformer

from src.embed import RetrievedChunk, VectorIndex
from src.utils import load_config, resolve_path, save_json, setup_logging

load_dotenv()
logger = setup_logging("orchestrate")

PipelineMode = Literal["local_llm", "api_llm", "reranked_gemini", "reranked_local", "extractive"]

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


@dataclass
class SourceMetadata:
    source_file: str
    doc_type: str
    section_hint: str
    similarity: float
    distance: float
    excerpt: str


@dataclass
class QueryResult:
    answer: str
    confidence: float
    sources: list[SourceMetadata]
    pipeline: str
    latency_ms: float
    retrieval_scores: list[float]


class RAGPipeline:
    def __init__(self, mode: PipelineMode = "reranked_local"):
        self.config = load_config()
        self.mode = mode
        self.retrieval_cfg = self.config["retrieval"]
        self.llm_cfg = self.config["llm"]
        self.guardrails = self.config["anti_hallucination"]

        embed_model = self.config["embedding"]["model_name"]
        self.embedder = SentenceTransformer(embed_model)
        self.index = VectorIndex(self.config["paths"]["vector_store_dir"])
        self.reranker: CrossEncoder | None = None
        if "reranked" in mode:
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def _retrieve(self, query: str) -> list[RetrievedChunk]:
        query_emb = self.embedder.encode(query, normalize_embeddings=True).tolist()
        candidates = self.index.query(query_emb, top_k=self.retrieval_cfg["top_k"])

        if self.reranker is not None:
            pairs = [[query, c.text] for c in candidates]
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

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
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

    def _compute_confidence(self, chunks: list[RetrievedChunk], answer: str) -> float:
        if not chunks:
            return 0.0
        abstain = self.guardrails["abstain_phrase"].lower()
        if abstain in answer.lower():
            return 0.1
        avg_sim = sum(c.similarity for c in chunks) / len(chunks)
        top_sim = max(c.similarity for c in chunks)
        return round(min(0.99, 0.5 * avg_sim + 0.5 * top_sim), 2)

    def _generate_gemini(self, prompt: str) -> str:
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
        """Deterministic fallback when LLM backend is unavailable."""
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

        query_terms = {t.lower() for t in query.split() if len(t) > 3}
        scored: list[tuple[int, str]] = []
        for line in lines:
            lower = line.lower()
            score = sum(1 for term in query_terms if term in lower)
            if score:
                scored.append((score, line))
        if scored:
            best = sorted(scored, key=lambda x: x[0], reverse=True)[:3]
            return " ".join(item[1] for item in best)

        summary = " ".join(lines[:4])
        return f"Based on retrieved documents: {summary[:800]}"

    def _generate(self, prompt: str, user_query: str) -> str:
        if self.mode == "extractive":
            return self._fallback_answer(user_query, prompt)

        provider = self.llm_cfg.get("provider", "ollama").lower()
        if provider == "gemini" and self.mode in {"api_llm", "reranked_gemini"}:
            try:
                return self._generate_gemini(prompt)
            except Exception as exc:
                logger.warning("Gemini failed (%s). Falling back to Ollama.", exc)
        return self._generate_ollama(prompt, user_query)

    def query(self, user_query: str) -> QueryResult:
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


def save_pipeline_state(mode: PipelineMode) -> None:
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
    payload = asdict(result)
    payload["sources"] = [asdict(s) for s in result.sources]
    return payload
