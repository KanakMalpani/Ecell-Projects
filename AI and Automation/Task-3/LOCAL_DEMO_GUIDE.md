# Local Demo Guide — Task 3 AI CRM

Quick start: run `.\start_demo.ps1` from the Task-3 folder.

## 1. Setup (one time)

```powershell
cd "C:\Users\mrkan\E-Cell\AI and Automation\Task-3"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run_pipeline.py
```

## 2. Start the server

```powershell
uvicorn api.app:app --host 127.0.0.1 --port 8002 --reload
```

Open:
- Swagger UI: http://127.0.0.1:8002/docs
- Dashboard: http://127.0.0.1:8002/dashboard

## 3. Authenticate

In Swagger, click **Authorize** and paste a token from:

```powershell
curl -X POST http://127.0.0.1:8002/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"agent1\",\"password\":\"agent123\"}"
```

Use `analytics1` / `analytics123` for HEART and cohort endpoints.

## 4. Demo script (evaluation day)

### A. Ticket summarization
1. GET `/api/v1/customers?limit=1` — copy a `customer_id`
2. POST `/api/v1/tickets/create` with that customer
3. POST `/api/v1/tickets/{ticket_id}/summarize`

### B. LangGraph agent
POST `/api/v1/query/agent`:
```json
{
  "customer_id": "CUST-XXXXXXXX",
  "query": "I was charged twice last month and still have an open technical ticket. What is the status and next step?"
}
```

### C. HEART dashboard
Open http://127.0.0.1:8002/dashboard — login as `analytics1`

### D. Cohort export
POST `/api/v1/cohorts/export/json` (analytics or supervisor token)

## 5. Optional LLM backends

**Ollama (local, default):**
```
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3:8b-instruct
```

## 6. Module-only runs

```powershell
python -m src.crm
python -m src.agents
python -m src.cohort
python -m src.heart
```
