"""
Ingest synthetic dataset JSON into the CRM SQLite database.

WHAT THIS FILE DOES
-------------------
  1. Reads data/synthetic_crm_dataset.json
  2. Clears existing DB tables (clean re-ingest)
  3. Calls crm_service.bulk_ingest() with deduplication

INGESTION SAFEGUARDS
--------------------
  - Skip duplicate customer emails
  - Skip duplicate ticket IDs
  - Skip tickets/interactions for non-existent customers
  - INSERT OR IGNORE for tickets prevents re-ingest crashes

RUN
---
  python scripts/run_ingest.py
  (or via: python run_pipeline.py)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.crm import crm_service
from src.database import get_db, init_db


def main() -> None:
    init_db()
    data_file = ROOT / "data" / "synthetic_crm_dataset.json"
    if not data_file.exists():
        print("Dataset not found. Run: python scripts/generate_data.py")
        sys.exit(1)

    payload = json.loads(data_file.read_text(encoding="utf-8"))

    # Clear existing for clean re-ingest
    with get_db() as conn:
        conn.execute("DELETE FROM interactions")
        conn.execute("DELETE FROM tickets")
        conn.execute("DELETE FROM customers")
        conn.execute("DELETE FROM customer_memory")

    stats = crm_service.bulk_ingest(payload)
    print("Ingestion complete:", stats)


if __name__ == "__main__":
    main()
