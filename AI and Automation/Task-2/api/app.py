"""
FastAPI deployment — Stage 5.

Serves the RAG pipeline as a REST API for live Q&A over company documents.

Start (after running run_pipeline.py):
    uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload

Endpoints:
    GET  /health  → server status + active pipeline name
    POST /query   → ask a question, get answer + sources + confidence

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

# Load the best pipeline mode saved by run_pipeline.py (e.g. "reranked_local")
if state_path.exists():
    with state_path.open(encoding="utf-8") as handle:
        saved_state = json.load(handle)
    ACTIVE_MODE = saved_state.get("active_pipeline", config["evaluation"]["default_pipeline"])
else:
    ACTIVE_MODE = config["evaluation"]["default_pipeline"]

# Create the RAG pipeline once at import time — reused for every request
pipeline = RAGPipeline(mode=ACTIVE_MODE)  # type: ignore[arg-type]

app = FastAPI(
    title="Enterprise Knowledge RAG API",
    description=(
        "Semantic retrieval and grounded Q&A over organizational documentation. "
        "Returns answers with confidence scores and verifiable source metadata."
    ),
    version="1.0.0",
)


class QueryRequest(BaseModel):
    """What the client sends to POST /query."""
    query: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Natural language question",
    )


class SourceItem(BaseModel):
    """One source citation in the response."""
    source_file: str
    doc_type: str
    section_hint: str
    similarity: float
    distance: float
    excerpt: str


class QueryResponse(BaseModel):
    """What the API returns after processing a question."""
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    sources: list[SourceItem]
    pipeline: str | None = None
    latency_ms: float | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness check — confirms server is running and which pipeline is active."""
    return {
        "status": "ok",
        "active_pipeline": ACTIVE_MODE,
    }


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest) -> QueryResponse:
    """
    Ask a natural language question about the enterprise document corpus.

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


@app.on_event("startup")
def on_startup() -> None:
    """Refresh pipeline_state.json on server start."""
    save_pipeline_state(ACTIVE_MODE)  # type: ignore[arg-type]
