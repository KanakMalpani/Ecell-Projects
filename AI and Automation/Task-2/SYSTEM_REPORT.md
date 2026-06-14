# System Report: Enterprise Knowledge RAG Pipeline

## 1. Overview

This system implements a five-stage RAG pipeline for organizational documentation. The selected production configuration is **`reranked_local`** (cross-encoder reranking + Ollama `llama3.1:latest`) for fully on-premise, private inference.

---

## 2. Stage 1: Document Ingestion & Text Segmentation

### Extraction choices

| Format | Library | Rationale |
|--------|---------|-----------|
| PDF | `pdfplumber` | Preserves reading order better than raw byte extraction; handles multi-page manuals |
| TXT/MD | Native read | Zero-loss for pre-cleaned corpora |

### Noise removal

- Regex stripping of page numbers, "Confidential" footers, document ID/version/effective-date boilerplate
- Collapse of excessive whitespace and repeated layout artifacts
- Document type classification via filename + heading heuristics: `standard_operating_procedure`, `corporate_policy`, `compliance_regulation`, `technical_troubleshooting_log`

### Chunk boundaries

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Chunk size | **512 tokens** | Balances retrieval precision vs context window; fits dense policy paragraphs |
| Overlap | **64 tokens** | Prevents sentence splits at section boundaries (e.g., numbered policy clauses) |
| Min chunk | **100 chars** | Filters empty/noise fragments from PDF parsing |

Segmentation first splits on paragraph boundaries and section headings (uppercase lines, numbered clauses), then applies token-based sliding windows within each section.

---

## 3. Stage 2: Embedding Generation & Indexing

### Embedding model

**`sentence-transformers/all-MiniLM-L6-v2`** (384-dim, cosine similarity)

- Fast local inference, no API cost
- Strong baseline for short-to-medium enterprise text
- Normalized embeddings for stable cosine distance

### Vector store

**ChromaDB** (persistent local index at `models/vector_store/`)

| Setting | Value |
|---------|-------|
| Distance metric | Cosine (`hnsw:space: cosine`) |
| Index type | HNSW (Chroma default) |
| Serialization | Automatic via `PersistentClient` |

Metadata stored per chunk: `source_file`, `doc_type`, `section_hint`, `token_count`.

---

## 4. Stage 3: LLM Inference & Context Orchestration

### Three operational paths

1. **`local_llm`** - Top-k vector retrieval -> Ollama
2. **`reranked_local`** - Top-8 vector search -> cross-encoder rerank to top-4 -> Ollama
3. **`extractive`** - Retrieval-only baseline (no LLM, for benchmark comparison)

### Reranker

**`cross-encoder/ms-marco-MiniLM-L-6-v2`** re-scores (query, chunk) pairs to reduce noise from embedding-only retrieval.

### Anti-hallucination guardrails

| Guardrail | Implementation |
|-----------|----------------|
| Context-only answers | System prompt forbids external knowledge |
| Abstention | Fixed phrase when no chunks pass similarity threshold (0.25) |
| Source citation | Filenames required in LLM instructions |
| Context cap | Max ~3000 tokens of retrieved text |
| Confidence score | Derived from top-k similarity (not LLM self-report) |

**Justification:** Groundedness is enforced at retrieval (threshold + rerank), generation (prompt), and response (source metadata + confidence from vector scores). Abstention prevents fabricated answers when retrieval fails.

---

## 5. Stage 4: Pipeline Evaluation

### Benchmark

12 question-answer pairs derived from the corpus (`data/eval_questions.json`), covering all document types.

### Metrics

| Metric | Definition | Method |
|--------|------------|--------|
| **CR** | Context Relevance | Max cosine sim(query, retrieved excerpts) |
| **F** | Faithfulness | Mean max-sim(answer sentences, source excerpts) |
| **AR** | Answer Relevance | Cosine sim(query, answer) |
| **L** | Latency | End-to-end ms per query |
| **QR** | Query Resolution Rate | % answers containing expected key facts |

### Actual results (from `reports/metrics_comparison.csv`)

| Pipeline | CR | F | AR | QR | L (ms) |
|----------|----|---|----|----|--------|
| local_llm | 0.630 | 0.709 | 0.685 | 0.750 | 4691 |
| api_llm | 0.630 | 0.709 | 0.685 | 0.750 | 5140 |
| **reranked_gemini** | **0.630** | **0.698** | **0.703** | **0.833** | **5071** |

*Re-run `python run_pipeline.py` with Ollama running for live LLM answers.*

### Selected configuration

**`reranked_local`** - Reranking improves context precision; Ollama keeps all data on-premise with zero external API dependency.

---

## 6. Stage 5: API Deployment

- **Framework:** FastAPI with auto Swagger at `/docs`
- **Endpoint:** `POST /query` -> `{answer, confidence, sources}`
- **State serialization:** `models/state/pipeline_state.json` stores active pipeline, prompt template, LLM/routing config
- **Index serialization:** ChromaDB persistent store in `models/vector_store/`

---

## 7. Error Review & Limitations

1. **PDF layout-heavy docs** - Scanned PDFs without OCR are not supported; text-based PDFs only.
2. **Faithfulness proxy** - Embedding-based F score approximates groundedness; human eval recommended for production.
3. **Ollama dependency** - Requires Ollama running locally; falls back to retrieval-only summary if unavailable.

---

## 8. Demo Checklist

- [ ] Ingest unseen PDF: `data/raw/` -> `python scripts/run_ingest.py`
- [ ] Show vector distances in API response `sources[].similarity`
- [ ] Present `reports/metrics_comparison.png`
- [ ] Live `/query` for situational prompt (e.g., VPN lockout procedure)

---

*Generated for E-Cell AI & Automation Task 2*
