"""SQLite persistence for CRM entities."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

from src.config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                company TEXT,
                industry TEXT,
                product_tier TEXT,
                acquisition_date TEXT,
                tenure_days INTEGER DEFAULT 0,
                engagement_score REAL DEFAULT 0,
                ticket_count INTEGER DEFAULT 0,
                behavioral_tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                cohort_id TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                status TEXT DEFAULT 'Open',
                assigned_agent TEXT,
                ai_assisted INTEGER DEFAULT 0,
                csat_score REAL,
                created_at TEXT,
                updated_at TEXT,
                resolved_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                channel TEXT,
                event_type TEXT,
                content TEXT,
                ticket_id TEXT,
                duration_minutes REAL,
                timestamp TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS customer_memory (
                customer_id TEXT PRIMARY KEY,
                short_term TEXT DEFAULT '[]',
                long_term TEXT DEFAULT '',
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                agent_id TEXT,
                role TEXT,
                payload TEXT,
                response_meta TEXT,
                latency_ms REAL,
                timestamp TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets(customer_id);
            CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
            CREATE INDEX IF NOT EXISTS idx_interactions_customer ON interactions(customer_id);
            CREATE INDEX IF NOT EXISTS idx_customers_cohort ON customers(cohort_id);
            """
        )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    for key in ("behavioral_tags", "metadata"):
        if key in data and isinstance(data[key], str):
            try:
                data[key] = json.loads(data[key])
            except json.JSONDecodeError:
                pass
    if "ai_assisted" in data:
        data["ai_assisted"] = bool(data["ai_assisted"])
    return data


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
