"""Application configuration loaded from environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
JWT_SECRET = os.getenv("JWT_SECRET", "ecell-crm-dev-secret")
DB_PATH = DATA_DIR / "crm.db"
