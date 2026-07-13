"""
Module 4 — Google HEART framework metrics from live CRM data.

WHAT THIS FILE DOES
-------------------
Computes all 5 dimensions of Google's HEART UX measurement framework
adapted for CRM product health — all metrics recompute from live SQLite
data on every API call (not cached or hardcoded).

HEART DIMENSIONS
----------------
  H — Happiness    : avg CSAT on resolved tickets; NPS proxy from engagement tiers
  E — Engagement   : active customers (engagement≥30), ticket open rate, interaction depth
  A — Adoption     : AI-assisted ticket rate, onboarding completion, memory usage
  R — Retention    : monthly retention (engagement≥25), churn flags, avg lifespan
  T — Task Success : resolution rate, FCR proxy, escalation rate, AI vs human ratio

WHY HEART (not just churn rate)?
--------------------------------
  Churn alone doesn't tell you WHY customers leave. HEART gives a balanced
  view: are customers happy (H), using the product (E), adopting AI features (A),
  staying (R), and succeeding at their tasks (T)?

PI INTERVIEW TALKING POINTS
---------------------------
  Q: What is NPS proxy here?
  A: (promoters - detractors) / N × 100, where promoter = engagement≥70,
     detractor = engagement<40. True NPS requires survey data.

  Q: What is FCR proxy?
  A: First Contact Resolution — non-escalated resolutions / total tickets.
     True FCR needs per-interaction tracking.

  Q: How is this exposed to users?
  A: GET /api/v1/heart API endpoint + live Chart.js dashboard at /dashboard.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np

from src.crm import crm_service
from src.database import get_db, row_to_dict


class HEARTService:
    """Compute Happiness, Engagement, Adoption, Retention, Task Success."""

    def compute_all(self, cohort_id: str | None = None) -> dict[str, Any]:
        return {
            "happiness": self.happiness(cohort_id),
            "engagement": self.engagement(cohort_id),
            "adoption": self.adoption(cohort_id),
            "retention": self.retention(cohort_id),
            "task_success": self.task_success(cohort_id),
            "computed_at": datetime.utcnow().isoformat() + "Z",
        }

    def _filter_customers(self, cohort_id: str | None) -> list[dict[str, Any]]:
        if cohort_id:
            return crm_service.list_customers(segment=cohort_id, limit=10000)
        return crm_service.list_customers(limit=10000)

    def _filter_tickets(self, customers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ids = {c["id"] for c in customers}
        return [t for t in crm_service.list_tickets() if t["customer_id"] in ids]

    def happiness(self, cohort_id: str | None = None) -> dict[str, Any]:
        customers = self._filter_customers(cohort_id)
        tickets = self._filter_tickets(customers)
        csat_scores = [t["csat_score"] for t in tickets if t.get("csat_score") is not None]
        avg_csat = round(float(np.mean(csat_scores)), 2) if csat_scores else round(
            float(np.mean([c.get("engagement_score", 50) for c in customers])), 2
        )

        by_category: dict[str, list[float]] = {}
        for t in tickets:
            if t.get("csat_score") is not None:
                by_category.setdefault(t.get("category", "general"), []).append(t["csat_score"])

        # NPS proxy from engagement tiers
        promoters = sum(1 for c in customers if c.get("engagement_score", 0) >= 70)
        detractors = sum(1 for c in customers if c.get("engagement_score", 0) < 40)
        n = len(customers) or 1
        nps = round(100 * (promoters - detractors) / n, 2)

        return {
            "avg_csat": avg_csat,
            "nps_proxy": nps,
            "csat_by_category": {k: round(float(np.mean(v)), 2) for k, v in by_category.items()},
            "sample_size": len(csat_scores) or len(customers),
        }

    def engagement(self, cohort_id: str | None = None) -> dict[str, Any]:
        customers = self._filter_customers(cohort_id)
        tickets = self._filter_tickets(customers)
        with get_db() as conn:
            rows = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()
        total_interactions = rows[0] if rows else 0

        open_rate = len([t for t in tickets if t["status"] == "Open"]) / max(len(tickets), 1)
        avg_engagement = round(float(np.mean([c.get("engagement_score", 0) for c in customers])), 2) if customers else 0

        return {
            "active_customers": len([c for c in customers if c.get("engagement_score", 0) >= 30]),
            "total_customers": len(customers),
            "ticket_open_rate": round(open_rate, 4),
            "avg_engagement_score": avg_engagement,
            "total_interactions": total_interactions,
            "avg_session_depth_proxy": round(total_interactions / max(len(customers), 1), 2),
        }

    def adoption(self, cohort_id: str | None = None) -> dict[str, Any]:
        customers = self._filter_customers(cohort_id)
        tickets = self._filter_tickets(customers)
        ai_tickets = sum(1 for t in tickets if t.get("ai_assisted"))
        onboarded = sum(1 for c in customers if c.get("tenure_days", 0) >= 7)

        with get_db() as conn:
            mem_rows = conn.execute("SELECT COUNT(*) FROM customer_memory").fetchone()
        memory_users = mem_rows[0] if mem_rows else 0

        n = len(customers) or 1
        return {
            "ai_assisted_ticket_rate": round(ai_tickets / max(len(tickets), 1), 4),
            "onboarding_completion_rate": round(onboarded / n, 4),
            "memory_adoption_rate": round(memory_users / n, 4),
            "feature_adoption_proxy": round((ai_tickets + memory_users) / (n + len(tickets) or 1), 4),
        }

    def retention(self, cohort_id: str | None = None) -> dict[str, Any]:
        customers = self._filter_customers(cohort_id)
        if not customers:
            return {"monthly_retention": 0, "avg_lifespan_days": 0, "churn_flags": 0}

        retained = sum(1 for c in customers if c.get("engagement_score", 0) >= 25)
        churn_flags = sum(1 for c in customers if c.get("engagement_score", 0) < 35 and c.get("ticket_count", 0) > 5)
        avg_tenure = round(float(np.mean([c.get("tenure_days", 0) for c in customers])), 1)

        return {
            "monthly_retention": round(retained / len(customers), 4),
            "avg_lifespan_days": avg_tenure,
            "churn_flags": churn_flags,
            "cohort_size": len(customers),
        }

    def task_success(self, cohort_id: str | None = None) -> dict[str, Any]:
        tickets = self._filter_tickets(self._filter_customers(cohort_id))
        if not tickets:
            return {"resolution_rate": 0, "fcr_rate": 0, "escalation_rate": 0}

        resolved = [t for t in tickets if t["status"] in ("Resolved", "Closed")]
        escalated = [t for t in tickets if t["status"] == "Escalated" or t.get("assigned_agent") == "AGT-ESC-01"]
        ai_resolved = [t for t in resolved if t.get("ai_assisted")]

        resolution_rate = len(resolved) / len(tickets)
        fcr = len([t for t in resolved if t.get("category") != "escalated"]) / len(tickets)
        escalation_rate = len(escalated) / len(tickets)

        return {
            "resolution_rate": round(resolution_rate, 4),
            "first_contact_resolution_proxy": round(fcr, 4),
            "escalation_rate": round(escalation_rate, 4),
            "ai_vs_human_resolution_ratio": round(
                len(ai_resolved) / max(len(resolved) - len(ai_resolved), 1), 4
            ),
            "total_tickets": len(tickets),
        }


heart_service = HEARTService()


def main() -> None:
    scores = heart_service.compute_all()
    for dim, data in scores.items():
        if dim != "computed_at":
            print(f"{dim.upper()}:", data)


if __name__ == "__main__":
    main()
