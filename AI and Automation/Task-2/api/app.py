"""
=============================================================================
Enterprise RAG API — Stage 5 (Deployment)
=============================================================================

PURPOSE
-------
Exposes the RAG pipeline as a production-ready REST API using FastAPI.
This is the final stage of the five-stage Enterprise Knowledge Management
pipeline: users send natural-language questions and receive grounded answers
with source citations and confidence scores.

ROLE IN THE RAG PIPELINE
------------------------
  Stage 1 (ingest)   → chunks.json
  Stage 2 (embed)    → ChromaDB vector index
  Stage 3 (orchestrate) → RAGPipeline.query()  ← THIS FILE CALLS THIS
  Stage 4 (evaluate) → picks best pipeline mode (e.g. reranked_local)
  Stage 5 (deploy)   → THIS FILE — serves /query over HTTP

The API loads the winning pipeline mode from pipeline_state.json (written by
run_pipeline.py after evaluation) and instantiates RAGPipeline once at startup
(singleton pattern) so model loading cost is paid once, not per request.

INTERVIEW TALKING POINTS
------------------------
1. **Why FastAPI?** Auto-generated OpenAPI/Swagger docs, Pydantic request
   validation, async-ready, type hints — ideal for demo and production.
2. **Singleton pipeline:** RAGPipeline loads SentenceTransformer + ChromaDB +
   optional CrossEncoder at import time; amortizes ~2–5s cold-start across all
   requests. Trade-off: cannot hot-swap pipeline mode without restart.
3. **State hydration:** Reads models/state/pipeline_state.json to pick the
   evaluation winner (reranked_local by default). Falls back to config default
   if state file missing (e.g. --skip-eval run).
4. **Error handling:** Internal exceptions become HTTP 500 with generic message
   (no stack trace leakage). Logs full traceback server-side via logger.exception.
5. **Response contract:** answer + confidence [0,1] + sources[] with similarity,
   distance, excerpt — enables UI citation chips and trust indicators.
6. **Anti-hallucination is upstream:** Guardrails live in orchestrate.py; API
   is a thin transport layer — separation of concerns for testability.
7. **Startup hook:** on_startup refreshes pipeline_state.json so deploy artifacts
   stay consistent even if evaluation was run separately.

START SERVER (after run_pipeline.py):
    uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload

ENDPOINTS:
    GET  /health  → liveness + active pipeline name
    POST /query   → grounded Q&A with sources

Swagger UI: http://127.0.0.1:8001/docs
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.orchestrate import RAGPipeline, result_to_dict, save_pipeline_state
from src.utils import load_config, resolve_path

logger = logging.getLogger("api")
config = load_config()
state_path = resolve_path(config["paths"]["state_dir"]) / "pipeline_state.json"

# ---------------------------------------------------------------------------
# Pipeline bootstrap — load evaluation winner once at module import
# ---------------------------------------------------------------------------
# Interview note: This runs before uvicorn accepts connections. If state file
# exists, we trust Stage 4's recommended_pipeline; otherwise use YAML default.
if state_path.exists():
    with state_path.open(encoding="utf-8") as handle:
        saved_state = json.load(handle)
    ACTIVE_MODE = saved_state.get("active_pipeline", config["evaluation"]["default_pipeline"])
else:
    ACTIVE_MODE = config["evaluation"]["default_pipeline"]

# Singleton RAGPipeline — reused for every /query request (models stay in RAM)
pipeline = RAGPipeline(mode=ACTIVE_MODE)  # type: ignore[arg-type]

# ---------------------------------------------------------------------------
# FastAPI application metadata (appears in Swagger /docs)
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Enterprise Knowledge RAG API",
    description=(
        "Semantic retrieval and grounded Q&A over organizational documentation. "
        "Returns answers with confidence scores and verifiable source metadata."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request/Response schemas (Pydantic) — contract for POST /query
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    """
    Incoming question payload for POST /query.

    Interview note: min_length=3 prevents empty/trivial queries; max_length=2000
    caps token cost sent to the LLM. Validation happens before pipeline.query().
    """
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question",
    )


class SourceItem(BaseModel):
    """
    One retrieved chunk citation returned to the client.

    similarity: 1 - cosine_distance (higher = better match)
    distance:   raw ChromaDB cosine distance (lower = better match)
    excerpt:    first ~240 chars of chunk — enough for UI preview without full text
    """
    source_file: str
    doc_type: str
    section_hint: str
    similarity: float
    distance: float
    excerpt: str


class QueryResponse(BaseModel):
    """
    Complete RAG response envelope.

    confidence: derived from retrieval similarity (see orchestrate._compute_confidence)
    pipeline:   which mode answered (local_llm, reranked_local, extractive, …)
    latency_ms: end-to-end wall time including retrieval + LLM
    """
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: list[SourceItem]
    pipeline: str | None = None
    latency_ms: float | None = None


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, Any]:
    """
    Liveness/readiness probe for load balancers and demo checks.

    Returns active_pipeline so operators know which RAG mode is serving traffic
    without triggering a full query (no LLM cost).
    """
    return {
        "status": "ok",
        "active_pipeline": ACTIVE_MODE,
    }


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest) -> QueryResponse:
    """
    Main RAG endpoint — ask a question, get a grounded answer.

    Flow:
      1. Strip whitespace from query
      2. Delegate to RAGPipeline.query() (retrieve → rerank → LLM → guardrails)
      3. Map QueryResult dataclass → QueryResponse Pydantic model

    Example request:
        {"query": "What is the minimum password length?"}

    Example response:
        {
          "answer": "The minimum password length is 14 characters.",
          "confidence": 0.87,
          "sources": [{"source_file": "corporate_security_policy.txt", ...}],
          "pipeline": "reranked_local",
          "latency_ms": 4200.0
        }

    Interview note: We catch all exceptions and return HTTP 500 — never expose
    internal errors to clients (security + UX). Full traceback logged server-side.
    """
    try:
        result = pipeline.query(request.query.strip())
    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing the query.",
        ) from exc

    payload = result_to_dict(result)
    return QueryResponse(
        answer=payload["answer"],
        confidence=payload["confidence"],
        sources=payload["sources"],
        pipeline=payload.get("pipeline"),
        latency_ms=payload.get("latency_ms"),
    )


# ---------------------------------------------------------------------------
# Lifecycle hooks
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    """
    Refresh pipeline_state.json when the server boots.

    Ensures deploy artifacts reflect the currently loaded ACTIVE_MODE even if
    evaluation was run in a separate process before uvicorn started.
    """
    save_pipeline_state(ACTIVE_MODE)  # type: ignore[arg-type]
