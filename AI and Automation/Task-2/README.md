# E-Cell AI & Automation - Task 2

End-to-end **knowledge management and semantic retrieval (RAG)** system over enterprise policy manuals, SOPs, compliance documents, and troubleshooting logs. Uses **Ollama** for fully local, private LLM inference.

## Setup

```bash
cd "AI and Automation/Task-2"
pip install -r requirements.txt
```

Install [Ollama](https://ollama.com) and ensure a model is available:

```bash
ollama pull llama3.1
ollama list
```

Default model in `config/settings.yaml`: `llama3.1:latest`

## Run pipeline

```bash
python run_pipeline.py
```

Individual stages:

```bash
python scripts/run_ingest.py
python scripts/run_embed.py
python scripts/run_evaluate.py
```

## Run API

```bash
uvicorn api.app:app --reload --port 8001
```

Swagger docs: http://127.0.0.1:8001/docs

### Example

```json
POST /query
{"query": "What is the minimum password length required by the security policy?"}
```

## Three pipeline paths (Ollama)

| Path | Retrieval | LLM | Description |
|------|-----------|-----|-------------|
| `local_llm` | Vector search | Ollama | Basic RAG, on-premise |
| `reranked_local` | Cross-encoder rerank + vector | Ollama | **Recommended** - best precision |
| `extractive` | Vector search | None (retrieval-only baseline) | Benchmark baseline |

## Evaluation metrics

CR, F, AR, L, QR - see `reports/metrics_comparison.csv` after running evaluation.

## Docs

- `SYSTEM_REPORT.md` - design and guardrails
- `LOCAL_DEMO_GUIDE.md` - live demo checklist
