# Security Notes — Task 3 AI CRM

This project is an **academic evaluation/demo** system. Before any public deployment, review every item below.

## Authentication

- Passwords are verified with **PBKDF2-SHA256** (120k iterations). Plaintext is never stored in memory after load.
- Demo accounts are configured via `CRM_DEMO_USERS` in `.env`. Override defaults before production.
- Set a strong, unique **`JWT_SECRET`** in `.env` (never commit `.env`).

## API hardening (implemented)

| Control | Status |
|---------|--------|
| JWT on protected endpoints | Yes |
| RBAC (Agent / Supervisor / Admin / Analytics) | Yes |
| Report download auth + path traversal block | Yes |
| CORS restricted to `ALLOWED_ORIGINS` | Yes |
| List endpoint max limit (`MAX_LIST_LIMIT`) | Yes |
| Parameterized SQL queries | Yes |

## Demo-only items (acceptable for submission)

- Default demo credentials documented in `README.md`
- SQLite file-based DB (not for production concurrency)
- No HTTPS termination (run behind reverse proxy in production)

## Files never committed

- `.env` (secrets)
- `data/crm.db` (local database)
- `data/synthetic_crm_dataset.json` (regenerate locally)

## Pre-demo checklist

1. Copy `.env.example` → `.env` and set `JWT_SECRET`
2. Run `python scripts/verify_all.py`
3. Start Ollama locally for LLM features
4. Bind API to `127.0.0.1` only unless intentionally exposing
