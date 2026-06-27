# Task 3 — Submission Package

Submit these artifacts for E-Cell AI & Automation Task 3 (deadline: 5 July).

## Required deliverables

| Item | Location | Format |
|------|----------|--------|
| Source code | [GitHub: KanakMalpani/Ecell-Projects](https://github.com/KanakMalpani/Ecell-Projects) → `AI and Automation/Task-3/` | Git repo |
| Presentation | `submission/Task-3-Presentation.pdf` | PDF |
| System report | `submission/SYSTEM_REPORT.pdf` | PDF |
| Live demo | FastAPI + dashboard (evaluator runs locally) | — |

## Submit the PDFs

Upload both files from `submission/`:
- `Task-3-Presentation.pdf`
- `SYSTEM_REPORT.pdf`

Regenerate before submitting (includes live metrics charts):

```powershell
cd "AI and Automation\Task-3"
.venv\Scripts\activate
python scripts/generate_submission_pdfs.py
```

## One-command demo (evaluation day)

```powershell
.\start_demo.ps1
```

Or manually:

```powershell
.venv\Scripts\activate
uvicorn api.app:app --host 127.0.0.1 --port 8002 --reload
```

Then open:
- http://127.0.0.1:8002/docs
- http://127.0.0.1:8002/dashboard

## Pre-flight checklist

- [ ] `python scripts/verify_all.py` — all checks pass
- [ ] Ollama running: `ollama serve` + `ollama pull llama3:8b-instruct`
- [ ] `.env` created from `.env.example` with unique `JWT_SECRET`
- [ ] Both submission PDFs regenerated
- [ ] GitHub repo pushed and link ready to share

## Demo credentials

| User | Password | Use for |
|------|----------|---------|
| agent1 | agent123 | Tickets, summarization, agent query |
| analytics1 | analytics123 | HEART dashboard, cohort analysis |

See [LOCAL_DEMO_GUIDE.md](LOCAL_DEMO_GUIDE.md) for step-by-step demo script.
