#!/usr/bin/env python
"""End-to-end verification for Task 3 CRM platform."""

from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def main() -> None:
    print("=== Task 3 Verification ===\n")

    # 1. Files
    print("1. Deliverables")
    required = [
        "README.md",
        "SYSTEM_REPORT.md",
        "submission/Task-3-Presentation.pdf",
        "submission/SYSTEM_REPORT.pdf",
        "api/app.py",
        "src/crm.py",
        "src/agents.py",
        "src/cohort.py",
        "src/heart.py",
        "dashboard/index.html",
        "requirements.txt",
        ".env.example",
    ]
    for f in required:
        check(f, (ROOT / f).exists())

    # 2. Database
    print("\n2. Dataset")
    db = ROOT / "data" / "crm.db"
    if db.exists():
        conn = sqlite3.connect(db)
        nc = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        nt = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        ni = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
        check("customers >= 500", nc >= 500, str(nc))
        check("tickets >= 1000", nt >= 1000, str(nt))
        check("interactions >= 2000", ni >= 2000, str(ni))
    else:
        check("crm.db exists", False, "run: python run_pipeline.py")

    # 3. Modules
    print("\n3. Module logic")
    from src.crm import crm_service, TICKET_STATUSES
    from src.agents import agent_workflow
    from src.cohort import cohort_engine
    from src.heart import heart_service
    from src.llm import llm_client

    check("LLM provider is ollama", llm_client.provider == "ollama")
    check("ticket statuses", len(TICKET_STATUSES) == 5)

    heart = heart_service.compute_all()
    for dim in ("happiness", "engagement", "adoption", "retention", "task_success"):
        check(f"HEART.{dim}", dim in heart)

    analysis = cohort_engine.full_analysis()
    check("cohort analysis", bool(analysis.get("cohorts")))
    check("churn model metrics", "f1" in analysis.get("churn_model_metrics", {}))
    f1 = analysis.get("churn_model_metrics", {}).get("f1", 0)
    check("churn model F1 > 0", f1 > 0, str(f1))

    cid = cohort_engine.largest_cohort()
    if cid:
        curve = cohort_engine.retention_curve(cid)
        rates = [p["retention_rate"] for p in curve]
        check("retention curve non-zero", max(rates) > 0, str(rates))

    customers = crm_service.list_customers(limit=1)
    if customers:
        cid = customers[0]["id"]
        result = agent_workflow.query_agent(cid, "Summarize my open support issues")
        check("agent query", bool(result.get("answer")))
        check("agent confidence", 0 <= result.get("confidence", 0) <= 1)
        tickets = crm_service.list_tickets(customer_id=cid)
        if tickets:
            summ = agent_workflow.summarize_ticket(tickets[0]["id"])
            check("ticket summarize", bool(summ.get("summary")))
    else:
        check("agent query", False, "no customers")

    # 4. PDF word density
    print("\n4. PDF content density")
    try:
        from pypdf import PdfReader
    except ImportError:
        print("  [SKIP] pypdf not installed - using file size check")
        pres = ROOT / "submission" / "Task-3-Presentation.pdf"
        report = ROOT / "submission" / "SYSTEM_REPORT.pdf"
        check("presentation pdf > 5KB", pres.stat().st_size > 5000, f"{pres.stat().st_size} bytes")
        check("system report pdf > 10KB", report.stat().st_size > 10000, f"{report.stat().st_size} bytes")
    else:
        for label, path in [("presentation", ROOT / "submission" / "Task-3-Presentation.pdf"),
                            ("system report", ROOT / "submission" / "SYSTEM_REPORT.pdf")]:
            reader = PdfReader(str(path))
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            words = len(text.split())
            pages = len(reader.pages)
            density = words / max(pages, 1)
            check(f"{label} pages", pages >= 5, str(pages))
            check(f"{label} word count", words >= 200, str(words))
            check(f"{label} words/page", density >= 30, f"{density:.0f}")

    # 5. Charts
    print("\n5. Charts")
    for chart in ("heart_metrics.png", "retention_curve.png"):
        p = ROOT / "reports" / chart
        check(chart, p.exists(), f"{p.stat().st_size if p.exists() else 0} bytes")

    # 6. API (if server running)
    print("\n6. API (optional - start uvicorn first)")
    try:
        import httpx
        base = "http://127.0.0.1:8002"
        r = httpx.get(f"{base}/health", timeout=2)
        check("health endpoint", r.status_code == 200)
        login = httpx.post(f"{base}/api/v1/auth/login", json={"username": "agent1", "password": "agent123"}, timeout=5)
        check("auth login", login.status_code == 200)
        if login.status_code == 200:
            token = login.json()["access_token"]
            h = {"Authorization": f"Bearer {token}"}
            check("create ticket path", httpx.post(f"{base}/api/v1/tickets/create", headers=h,
                json={"customer_id": customers[0]["id"], "title": "Verify test", "description": "auto"},
                timeout=10).status_code == 200)
        analytics = httpx.post(f"{base}/api/v1/auth/login", json={"username": "analytics1", "password": "analytics123"}, timeout=5)
        if analytics.status_code == 200:
            h2 = {"Authorization": f"Bearer {analytics.json()['access_token']}"}
            check("heart endpoint", httpx.get(f"{base}/api/v1/heart", headers=h2, timeout=30).status_code == 200)
            check("cohort endpoint", httpx.get(f"{base}/api/v1/cohorts/analysis", headers=h2, timeout=60).status_code == 200)
    except Exception as exc:
        print(f"  [SKIP] API not running: {exc}")

    print("\n=== Summary ===")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s)")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("All checks passed.")


if __name__ == "__main__":
    main()
