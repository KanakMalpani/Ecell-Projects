"""E-Cell CRM platform — core Python package (src/).

PACKAGE CONTENTS (5 modules)
----------------------------
  src/crm.py      — Module 1: Customer & ticket management
  src/agents.py   — Module 2: LangGraph agent + ticket summarization
  src/memory.py   — Module 2: Per-customer conversation memory
  src/llm.py      — Module 2: Ollama/Gemini/Mock LLM abstraction
  src/cohort.py   — Module 3: Cohort retention + churn analysis
  src/heart.py    — Module 4: HEART framework metrics
  src/auth.py     — Module 5: JWT + RBAC authentication
  src/database.py — Shared SQLite persistence layer
  src/config.py   — Environment configuration from .env
  src/security.py — Path traversal protection for report downloads

Run any module standalone: python -m src.crm
"""
