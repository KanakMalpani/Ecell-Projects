# E-Cell Task 3 — AI-Integrated CRM Platform

Enterprise-style CRM for the fictional E-Cell company with LLM-powered ticket intelligence, LangGraph agents, cohort analysis, and a HEART metrics dashboard.

## Quick Start

```bash
cd "C:\Users\mrkan\E-Cell\AI and Automation\Task-3"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run_pipeline.py
uvicorn api.app:app --host 127.0.0.1 --port 8002 --reload
```

- **Swagger API docs:** http://127.0.0.1:8002/docs  
- **HEART Dashboard:** http://127.0.0.1:8002/dashboard  

## Demo Credentials

| Username     | Password       | Role       |
|-------------|----------------|------------|
| agent1      | agent123       | Agent      |
| supervisor1 | super123       | Supervisor |
| admin1      | admin123       | Admin      |
| analytics1  | analytics123   | Analytics  |

## Architecture (5 Modules)

| Module | Path | Description |
|--------|------|-------------|
| 1 — CRM | `src/crm.py` | Customer/ticket CRUD, lifecycle, segmentation, timeline, bulk ingest |
| 2 — AI | `src/agents.py`, `src/memory.py` | LangChain summarization, LangGraph routing agent, interaction memory |
| 3 — Cohort | `src/cohort.py` | Retention curves, churn scoring, JSON/PDF export |
| 4 — HEART | `src/heart.py` | Happiness, Engagement, Adoption, Retention, Task Success |
| 5 — API | `api/app.py` | FastAPI `/api/v1/*`, RBAC, audit metadata |

## Core API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/customers` | Create customer |
| POST | `/api/v1/tickets/create` | Create ticket |
| POST | `/api/v1/tickets/{id}/summarize` | LLM ticket summary |
| POST | `/api/v1/query/agent` | LangGraph agent query |
| GET | `/api/v1/cohorts/analysis` | Cohort retention & churn |
| GET | `/api/v1/heart` | HEART metrics |

All protected endpoints require `Authorization: Bearer <token>` from `/api/v1/auth/login`.

## LLM Configuration (Ollama — default)

This project uses **local Ollama** for all AI inference (Option A from the task spec).

1. Install [Ollama](https://ollama.com) and pull the model:
   ```bash
   ollama pull llama3:8b-instruct
   ```
2. Copy env file: `copy .env.example .env`
3. Ensure `LLM_PROVIDER=ollama` in `.env`

If Ollama is offline, the system falls back to a rule-based mock so demos still run.

Optional: set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY` for API mode.

## Synthetic Dataset

- **520** customer profiles  
- **1,050** support tickets  
- **2,500** interaction logs over ~6 months  

Generate: `python scripts/generate_data.py`  
Ingest: `python scripts/run_ingest.py`

## Verify & regenerate submission

```bash
python scripts/verify_all.py
python scripts/generate_submission_pdfs.py
```

Start Ollama before evaluation for live LLM responses: `ollama serve` and `ollama pull llama3:8b-instruct`.

## Run Modules Independently

```bash
python -m src.crm
python -m src.agents
python -m src.memory
python -m src.cohort
python -m src.heart
```

## Deliverables

- `SYSTEM_REPORT.md` — architecture, HEART definitions, cohort methodology, agent design  
- `SECURITY.md` — auth, secrets, and deployment hardening  
- `reports/` — exported cohort JSON/PDF  
- `data/synthetic_crm_dataset.json` — generated dataset  

## Evaluation Demo Checklist

1. Create ticket → summarize via `/api/v1/tickets/{id}/summarize`  
2. Multi-turn agent query via `/api/v1/query/agent`  
3. Open dashboard for live HEART + retention curves  
4. Export cohort report via `/api/v1/cohorts/export/json`  
