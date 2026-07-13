"""
Module 3 — Cohort analysis: retention curves, churn scoring, report export.

WHAT THIS FILE DOES
-------------------
Groups customers into cohorts, computes retention over 6 monthly periods,
scores churn risk per customer, validates with logistic regression, and
exports JSON/PDF reports.

COHORT ID FORMULA
-----------------
  cohort_id = {acquisition_month}_{industry}_{product_tier}
  Example: 2025-11_FinTech_Enterprise

RETENTION CURVE
---------------
  For each cohort, 6 periods (M+0 to M+5):
  - Customer "active" if: engagement_score - ticket_penalty >= threshold
  - Threshold decays: max(25, 78 - period * 9)
  - Retention rate = active / cohort_size

CHURN HEURISTIC
---------------
  churn_prob = 0.5*(1 - engagement/100) + 0.3*min(tickets/15,1) + 0.2*(1 - tenure/365)
  Flagged if churn_prob >= 0.6

ML VALIDATION (train_churn_model)
---------------------------------
  Logistic regression on engagement, tickets, tenure.
  Labels: top 25% heuristic scores = churn (75th percentile cutoff).
  Reports precision, recall, F1 on 75/25 stratified train/test split.

PI INTERVIEW TALKING POINTS
---------------------------
  Q: Why cohort analysis?
  A: Aggregate metrics hide segment problems — cohorts reveal whether Enterprise
     FinTech customers retain better than Starter SaaS customers.

  Q: Is the churn model production-ready?
  A: It's a validation baseline using heuristic-derived labels. Real production
     needs actual cancellation/churn event labels from billing data.

  Q: What libraries power the analytics?
  A: pandas for data manipulation, numpy for math, scikit-learn for logistic
     regression, reportlab for PDF export.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from src.config import REPORTS_DIR
from src.crm import crm_service
from src.database import get_db, row_to_dict
from src.heart import heart_service


class CohortEngine:
    """Segment customers, compute retention, and predict churn."""

    def list_cohorts(self) -> list[str]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT DISTINCT cohort_id FROM customers WHERE cohort_id IS NOT NULL"
            ).fetchall()
        return [r[0] for r in rows if r[0]]

    def cohort_customers(self, cohort_id: str) -> list[dict[str, Any]]:
        return crm_service.list_customers(segment=cohort_id, limit=10000)

    def largest_cohort(self) -> str | None:
        cohorts = self.list_cohorts()
        if not cohorts:
            return None
        return max(cohorts, key=lambda cid: len(self.cohort_customers(cid)))

    def retention_curve(self, cohort_id: str, periods: int = 6) -> list[dict[str, float]]:
        customers = self.cohort_customers(cohort_id)
        if not customers:
            return []

        curve = []
        total = len(customers)
        for period in range(periods):
            active = 0
            eng_threshold = max(25, 78 - period * 9)
            for c in customers:
                eng = c.get("engagement_score", 0)
                tickets = c.get("ticket_count", 0)
                ticket_penalty = min(tickets * period * 0.4, 12)
                if eng - ticket_penalty >= eng_threshold:
                    active += 1
            rate = round(active / total, 4) if total else 0.0
            curve.append({
                "period": period,
                "month_offset": period,
                "retention_rate": rate,
                "active": active,
                "total": total,
            })
        return curve

    def churn_scores(self, cohort_id: str | None = None) -> list[dict[str, Any]]:
        customers = self.cohort_customers(cohort_id) if cohort_id else crm_service.list_customers(limit=10000)
        scores = []
        for c in customers:
            prob = self._heuristic_churn(c)
            scores.append({
                "customer_id": c["id"],
                "cohort_id": c.get("cohort_id"),
                "churn_probability": round(prob, 4),
                "churn_flag": prob >= 0.6,
                "signals": self._churn_signals(c),
            })
        return scores

    def _heuristic_churn(self, customer: dict[str, Any]) -> float:
        eng = customer.get("engagement_score", 50) / 100
        tickets = min(customer.get("ticket_count", 0) / 15, 1.0)
        tenure_factor = min(customer.get("tenure_days", 0) / 365, 1.0)
        # Higher tickets + lower engagement => higher churn
        raw = 0.5 * (1 - eng) + 0.3 * tickets + 0.2 * (1 - tenure_factor)
        return float(np.clip(raw, 0.05, 0.95))

    def _churn_signals(self, customer: dict[str, Any]) -> list[str]:
        signals = []
        if customer.get("engagement_score", 100) < 40:
            signals.append("low_engagement")
        if customer.get("ticket_count", 0) > 8:
            signals.append("high_ticket_frequency")
        if customer.get("tenure_days", 0) < 60:
            signals.append("early_lifecycle")
        open_tickets = len([t for t in crm_service.list_tickets(customer_id=customer["id"]) if t["status"] in ("Open", "Escalated")])
        if open_tickets >= 2:
            signals.append("unresolved_backlog")
        return signals

    def train_churn_model(self) -> dict[str, float]:
        customers = crm_service.list_customers(limit=10000)
        if len(customers) < 50:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "note": "insufficient_data"}

        scores = [self._heuristic_churn(c) for c in customers]
        cutoff = float(np.percentile(scores, 75))
        rows = []
        for c, score in zip(customers, scores):
            rows.append({
                "engagement": c.get("engagement_score", 0),
                "tickets": c.get("ticket_count", 0),
                "tenure": c.get("tenure_days", 0),
                "label": 1 if score >= cutoff else 0,
            })
        df = pd.DataFrame(rows)
        X = df[["engagement", "tickets", "tenure"]]
        y = df["label"]
        stratify = y if y.nunique() > 1 and y.sum() >= 5 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=stratify,
        )
        model = LogisticRegression(max_iter=500)
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        precision, recall, f1, _ = precision_recall_fscore_support(
            y_test, preds, average="binary", zero_division=0,
        )
        return {
            "precision": round(float(precision), 4),
            "recall": round(float(recall), 4),
            "f1": round(float(f1), 4),
            "churn_label_cutoff": round(cutoff, 4),
            "flagged_customers": int((df["label"] == 1).sum()),
        }

    def resolution_metrics(self, cohort_id: str | None = None) -> dict[str, Any]:
        customers = self.cohort_customers(cohort_id) if cohort_id else crm_service.list_customers(limit=10000)
        cust_ids = {c["id"] for c in customers}
        tickets = [t for t in crm_service.list_tickets() if t["customer_id"] in cust_ids]

        resolved = [t for t in tickets if t["status"] in ("Resolved", "Closed")]
        times = []
        for t in resolved:
            if t.get("created_at") and t.get("resolved_at"):
                try:
                    c = datetime.fromisoformat(t["created_at"].replace("Z", ""))
                    r = datetime.fromisoformat(t["resolved_at"].replace("Z", ""))
                    times.append((r - c).total_seconds() / 3600)
                except ValueError:
                    pass

        by_category: dict[str, list[float]] = {}
        for t in resolved:
            if t.get("created_at") and t.get("resolved_at"):
                try:
                    c = datetime.fromisoformat(t["created_at"].replace("Z", ""))
                    r = datetime.fromisoformat(t["resolved_at"].replace("Z", ""))
                    hrs = (r - c).total_seconds() / 3600
                    by_category.setdefault(t.get("category", "general"), []).append(hrs)
                except ValueError:
                    pass

        return {
            "total_tickets": len(tickets),
            "resolved_count": len(resolved),
            "avg_resolution_hours": round(float(np.mean(times)), 2) if times else 0,
            "by_category_avg_hours": {k: round(float(np.mean(v)), 2) for k, v in by_category.items()},
        }

    def full_analysis(self, cohort_id: str | None = None) -> dict[str, Any]:
        cohorts = [cohort_id] if cohort_id else self.list_cohorts()[:10]
        if not cohorts:
            cohorts = ["default"]

        analyses = []
        for cid in cohorts:
            curve = self.retention_curve(cid)
            churn_rate = 1 - curve[-1]["retention_rate"] if curve else 0.0
            analyses.append({
                "cohort_id": cid,
                "retention_curve": curve,
                "churn_rate": round(churn_rate, 4),
                "customer_count": len(self.cohort_customers(cid)),
                "resolution_metrics": self.resolution_metrics(cid),
                "churn_scores_sample": self.churn_scores(cid)[:20],
            })

        model_metrics = self.train_churn_model()
        heart = heart_service.compute_all()

        return {
            "cohorts": analyses,
            "churn_model_metrics": model_metrics,
            "heart_scores": heart,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }

    def export_json(self, cohort_id: str | None = None) -> Path:
        data = self.full_analysis(cohort_id)
        path = REPORTS_DIR / f"cohort_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def export_pdf(self, cohort_id: str | None = None) -> Path:
        data = self.full_analysis(cohort_id)
        path = REPORTS_DIR / f"cohort_analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        c = canvas.Canvas(str(path), pagesize=letter)
        width, height = letter
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "E-Cell CRM — Cohort Analysis Report")
        y -= 30
        c.setFont("Helvetica", 10)
        for cohort in data.get("cohorts", [])[:5]:
            c.drawString(50, y, f"Cohort: {cohort['cohort_id']} | Customers: {cohort['customer_count']} | Churn: {cohort['churn_rate']:.1%}")
            y -= 15
            if y < 80:
                c.showPage()
                y = height - 50
        c.drawString(50, y - 20, f"Churn model F1: {data.get('churn_model_metrics', {}).get('f1', 'N/A')}")
        c.save()
        return path


cohort_engine = CohortEngine()


def main() -> None:
    analysis = cohort_engine.full_analysis()
    print("Cohorts:", len(analysis.get("cohorts", [])))
    if analysis.get("cohorts"):
        c = analysis["cohorts"][0]
        print("Sample cohort:", c["cohort_id"], "churn:", c["churn_rate"])
    print("Churn model:", analysis.get("churn_model_metrics"))


if __name__ == "__main__":
    main()
