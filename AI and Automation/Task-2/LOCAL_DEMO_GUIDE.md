# Local Demo Guide - Task 2

## 1. Setup

```bash
cd "AI and Automation/Task-2"
pip install -r requirements.txt
ollama pull llama3.1
```

Ensure Ollama is running (`ollama list`).

## 2. Build index

```bash
python run_pipeline.py
```

## 3. Start API

```bash
uvicorn api.app:app --reload --port 8001
```

http://127.0.0.1:8001/docs

## 4. Demo queries

- "What is the minimum password length required by the security policy?"
- "VPN shows Authentication Failed because account is locked - what do I do?"
- "Within how many days must GDPR breach be reported?"

Show `sources[].similarity` and `sources[].source_file` in each response.

## 5. Ingest unseen document

1. Add a `.txt` or `.pdf` to `data/raw/`
2. `python scripts/run_ingest.py && python scripts/run_embed.py`
3. Query the new content

## 6. Evaluation artifacts

- `reports/metrics_comparison.csv`
- `reports/metrics_comparison.png`
- `SYSTEM_REPORT.md`
