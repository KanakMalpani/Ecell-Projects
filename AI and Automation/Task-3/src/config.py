# -*- coding: utf-8 -*-
"""Application configuration loaded from environment."""

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
