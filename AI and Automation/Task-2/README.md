# E-Cell AI & Automation - Task 2

End-to-end **knowledge management and semantic retrieval (RAG)** system for enterprise policy manuals, SOPs, compliance documents, and troubleshooting logs.

**Repository:** [KanakMalpani/Ecell-Projects](https://github.com/KanakMalpani/Ecell-Projects) → `AI and Automation/Task-2/`

All LLM inference runs locally via **Ollama** — no cloud API keys required, no document data leaves your machine.

---

## Features

- Five-stage pipeline: ingest → embed → orchestrate → evaluate → deploy
- ChromaDB vector index with semantic search and cross-encoder reranking
- Anti-hallucination guardrails (context-only answers, abstention, source citations)
- FastAPI `/query` endpoint with Swagger docs
- Benchmark comparison across three pipeline paths

## Folder structure

```
Task-2/
├── api/app.py              # FastAPI deployment (Stage 5)
├── config/settings.yaml    # Chunk sizes, models, guardrails
├── data/raw/               # Source PDFs and text corpus
├── scripts/                # Per-stage entry points
├── src/                    # Core pipeline modules
├── models/                 # Vector index & state (generated, gitignored)
└── reports/                # Evaluation output (generated, gitignored)
```

## Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running

```bash
ollama pull llama3.1
ollama list
```

Default model: `llama3.1:latest` (set in `config/settings.yaml`)

## Setup

```bash
cd "AI and Automation/Task-2"
pip install -r requirements.txt
```

No `.env` file is required for the default Ollama setup. Optional `.env.example` is provided for future configuration only.

## Run pipeline

Build the index and run evaluation:

```bash
python run_pipeline.py
```

Individual stages:

```bash
python scripts/run_ingest.py
python scripts/run_embed.py
python scripts/run_evaluate.py
```

## Run API (local only)

Bind to localhost for development and demos:

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload
```

Swagger UI: http://127.0.0.1:8001/docs

### Example request

```http
POST /query
Content-Type: application/json

{"query": "What is the minimum password length required by the security policy?"}
```

### Example response

```json
{
  "answer": "The minimum password length is 14 characters (corporate_security_policy.txt).",
  "confidence": 0.87,
  "sources": [
    {
      "source_file": "corporate_security_policy.txt",
      "doc_type": "corporate_policy",
      "section_hint": "2. PASSWORD REQUIREMENTS",
      "similarity": 0.82,
      "distance": 0.18,
      "excerpt": "All user accounts must use passwords with a minimum length of 14 characters..."
    }
  ],
  "pipeline": "reranked_local",
  "latency_ms": 4200.0
}
```

## Pipeline paths

| Path | Retrieval | LLM | Description |
|------|-----------|-----|-------------|
| `local_llm` | Vector search | Ollama | Basic on-premise RAG |
| `reranked_local` | Cross-encoder rerank + vector | Ollama | **Recommended** — best precision |
| `extractive` | Vector search | None | Retrieval-only benchmark baseline |

## Evaluation metrics

| Metric | Meaning |
|--------|---------|
| CR | Context Relevance |
| F | Faithfulness (groundedness) |
| AR | Answer Relevance |
| L | Inference latency (ms) |
| QR | Query resolution rate |

Results: `reports/metrics_comparison.csv` (after running evaluation)

## Security

This project is designed for **local development and evaluation demos**.

| Control | Implementation |
|---------|----------------|
| No secrets in repo | `.env` is gitignored; no API keys required for Ollama |
| Local-only LLM | Ollama runs on `localhost:11434`; documents never sent to cloud |
| Local-only API | README instructs `--host 127.0.0.1`; do not expose publicly without auth |
| Input limits | Queries capped at 2,000 characters |
| Error handling | Internal errors are logged server-side; generic message returned to clients |
| Generated artifacts | Vector stores and pipeline state are gitignored |

**Do not** deploy this API to the public internet without adding authentication, HTTPS, and rate limiting.

Sample documents in `data/raw/` are fictional enterprise policies for demonstration — they contain no real credentials or PII.

## Adding documents

Drop `.txt` or `.pdf` files into `data/raw/`, then:

```bash
python scripts/run_ingest.py
python scripts/run_embed.py
```

## Documentation

- [`SYSTEM_REPORT.md`](SYSTEM_REPORT.md) — architecture, chunking choices, guardrails
- [`LOCAL_DEMO_GUIDE.md`](LOCAL_DEMO_GUIDE.md) — live demo checklist

## Deliverables

1. Source code (this folder)
2. System report (`SYSTEM_REPORT.md`)
3. Live demo via FastAPI `/query`
