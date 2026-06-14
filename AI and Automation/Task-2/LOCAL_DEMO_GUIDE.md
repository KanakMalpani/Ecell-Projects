# Local Demo Guide - Task 2

## 1. Setup

```bash
cd "AI and Automation/Task-2"
pip install -r requirements.txt
ollama pull llama3.1
ollama list   # confirm Ollama is running
```

## 2. Build index

```bash
python run_pipeline.py
```

## 3. Start API

```bash
uvicorn api.app:app --host 127.0.0.1 --port 8001 --reload
```

http://127.0.0.1:8001/docs

## 4. Demo queries

| Query | Expected source |
|-------|-----------------|
| Minimum password length? | corporate_security_policy.txt |
| VPN account locked? | vpn_troubleshooting_log.txt |
| GDPR breach reporting deadline? | gdpr_compliance_regulation.txt |
| Tier-1 RTO for backups? | backup_recovery_sop.pdf |

Show `sources[].similarity` and `sources[].distance` in each response.

## 5. Dynamic PDF ingestion demo

```bash
python scripts/create_sample_pdf.py
python scripts/run_ingest.py && python scripts/run_embed.py
```

Then ask: *"What is the RTO for Tier-1 systems?"*

## 6. Submission artifacts

| File | Purpose |
|------|---------|
| `submission/Task-2-Presentation.pdf` | PPT submission (required) |
| `submission/SYSTEM_REPORT.pdf` | System report PDF |
| `reports/metrics_comparison.csv` | Evaluation metrics |
| `reports/metrics_comparison.png` | Metrics chart |

Regenerate after evaluation:

```bash
python scripts/generate_submission_pdfs.py
```

## 7. Evaluation day checklist

- [ ] Ollama running (`ollama list`)
- [ ] API on 127.0.0.1:8001
- [ ] Presentation PDF ready in `submission/`
- [ ] GitHub repo link: https://github.com/KanakMalpani/Ecell-Projects
