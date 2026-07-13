"""
Main pipeline — generate synthetic data, ingest into CRM, optionally start API.

WHAT THIS FILE DOES
-------------------
Orchestrates the full data setup in two steps:
  Step 1: scripts/generate_data.py  → creates synthetic_crm_dataset.json
  Step 2: scripts/run_ingest.py     → loads JSON into SQLite (data/crm.db)
  Step 3 (optional): starts uvicorn API server

USAGE
-----
  python run_pipeline.py              # generate + ingest only
  python run_pipeline.py --serve      # generate + ingest + start API
  python run_pipeline.py --skip-generate  # ingest existing JSON only

PI INTERVIEW TALKING POINTS
---------------------------
  Q: Why a pipeline script?
  A: One command sets up the entire demo environment — evaluators don't need
     to know individual script names.

  Q: What data gets generated?
  A: 520 customers, 1050 tickets, 2500 interactions over ~6 months.
     Seeded random (seed=42) for reproducibility.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="E-Cell CRM pipeline")
    parser.add_argument("--serve", action="store_true", help="Start FastAPI after ingest")
    parser.add_argument("--skip-generate", action="store_true", help="Skip data generation")
    args = parser.parse_args()

    if not args.skip_generate:
        print("=== Step 1: Generate synthetic dataset ===")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_data.py")], check=True)

    print("=== Step 2: Ingest into CRM database ===")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "run_ingest.py")], check=True)

    if args.serve:
        print("=== Step 3: Starting API server ===")
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "api.app:app", "--host", "127.0.0.1", "--port", "8002", "--reload"],
            cwd=str(ROOT),
        )
    else:
        print("\nDone. Start API with:")
        print("  uvicorn api.app:app --host 127.0.0.1 --port 8002 --reload")
        print("Swagger: http://127.0.0.1:8002/docs")
        print("Dashboard: http://127.0.0.1:8002/dashboard")


if __name__ == "__main__":
    main()
