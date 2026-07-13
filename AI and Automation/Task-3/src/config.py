# -*- coding: utf-8 -*-
"""
Application configuration — loads all settings from .env file.

WHAT THIS FILE DOES
-------------------
Central config module: reads environment variables via python-dotenv and
exposes them as module-level constants used across the entire Task-3 project.

KEY SETTINGS
------------
  LLM_PROVIDER     — "ollama" (default) | "gemini" | falls back to mock
  OLLAMA_BASE_URL  — http://127.0.0.1:11434 (local Ollama server)
  OLLAMA_MODEL     — llama3:8b-instruct (8B parameter instruct-tuned model)
  GEMINI_API_KEY   — optional Google Gemini API key for cloud inference
  JWT_SECRET       — signs API bearer tokens; MUST change before production
  ALLOWED_ORIGINS  — CORS whitelist (localhost:8002 by default)
  DB_PATH          — data/crm.db (SQLite file location)
  MAX_LIST_LIMIT   — caps list endpoints at 500 to prevent abuse

PI INTERVIEW TALKING POINTS
---------------------------
  Q: Why load config at import time?
  A: Simple pattern for demo; all modules import from src.config directly.
     Production would use pydantic-settings with validation.

  Q: What happens with default JWT_SECRET?
  A: Logger warns at startup — acceptable for local demo, blocked in production.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
(MODELS_DIR / "state").mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_DEFAULT_JWT = "ecell-crm-dev-secret-change-in-production"
JWT_SECRET = os.getenv("JWT_SECRET", _DEFAULT_JWT)
if JWT_SECRET == _DEFAULT_JWT:
    logger.warning(
        "Using default JWT_SECRET; set a strong JWT_SECRET in .env before public deployment."
    )

CRM_ENV = os.getenv("CRM_ENV", "development").lower()
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://127.0.0.1:8002,http://localhost:8002",
    ).split(",")
    if o.strip()
]

DB_PATH = DATA_DIR / "crm.db"
MAX_LIST_LIMIT = int(os.getenv("MAX_LIST_LIMIT", "500"))
