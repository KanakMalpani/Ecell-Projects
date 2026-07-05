"""
Module 1 — Customer & Ticket Management.

CRUD, lifecycle states, segmentation, timeline views, bulk ingestion.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from src.database import get_db, init_db, now_iso, row_to_dict

TICKET_STATUSES = ("Open", "In Progress", "Escalated", "Resolved", "Closed")
VALID_TRANSITIONS: dict[str, set[str]] = {
    "Open": {"In Progress", "Escalated", "Closed"},
    "In Progress": {"Escalated", "Resolved", "Closed"},
    "Escalated": {"In Progress", "Resolved", "Closed"},
    "Resolved": {"Closed", "Open"},
    "Closed": {"Open"},
}

INDUSTRIES = ("SaaS", "FinTech", "HealthTech", "E-Commerce", "EdTech", "Manufacturing")
PRODUCT_TIERS = ("Starter", "Growth", "Enterprise")


class CRMService:
    def __init__(self) -> None:
        init_db()

    # ── Customers ──────────────────────────────────────────────────────────

    def create_customer(self, data: dict[str, Any]) -> dict[str, Any]:
        customer_id = data.get("id") or f"CUST-{uuid.uuid4().hex[:8].upper()}"
        tags = data.get("behavioral_tags", [])
        metadata = data.get("metadata", {})
        cohort_id = self._assign_cohort(data)
        ts = now_iso()
        record = {
            "id": customer_id,
            "name": data["name"],
            "email": data["email"],
            "company": data.get("company", ""),
            "industry": data.get("industry", "SaaS"),
            "product_tier": data.get("product_tier", "Starter"),
            "acquisition_date": data.get("acquisition_date", ts[:10]),
            "tenure_days": int(data.get("tenure_days", 0)),
            "engagement_score": float(data.get("engagement_score", 50.0)),
            "ticket_count": int(data.get("ticket_count", 0)),
            "behavioral_tags": json.dumps(tags if isinstance(tags, list) else []),
            "metadata": json.dumps(metadata if isinstance(metadata, dict) else {}),
            "cohort_id": cohort_id,
            "created_at": ts,
            "updated_at": ts,
        }
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO customers
                (id, name, email, company, industry, product_tier, acquisition_date,
                 tenure_days, engagement_score, ticket_count, behavioral_tags, metadata,
                 cohort_id, created_at, updated_at)
                VALUES (:id, :name, :email, :company, :industry, :product_tier,
                        :acquisition_date, :tenure_days, :engagement_score, :ticket_count,
                        :behavioral_tags, :metadata, :cohort_id, :created_at, :updated_at)
                """,
                record,
            )
        out = dict(record)
        out["behavioral_tags"] = tags
        out["metadata"] = metadata
        out["status"] = "active"
        return out

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        return row_to_dict(row)

    def list_customers(
        self,
        industry: str | None = None,
        segment: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM customers WHERE 1=1"
        params: list[Any] = []
        if industry:
            query += " AND industry = ?"
            params.append(industry)
        if segment:
            query += " AND cohort_id = ?"
            params.append(segment)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()
        return [row_to_dict(r) for r in rows if r]

    def update_customer(self, customer_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.get_customer(customer_id)
        if not existing:
            return None
        allowed = {
            "name", "company", "industry", "product_tier", "engagement_score",
            "behavioral_tags", "metadata", "tenure_days",
        }
        for key, value in updates.items():
            if key not in allowed:
                continue
            if key in ("behavioral_tags", "metadata"):
                existing[key] = value
            else:
                existing[key] = value
        existing["updated_at"] = now_iso()
        with get_db() as conn:
            conn.execute(
                """
                UPDATE customers SET name=?, company=?, industry=?, product_tier=?,
                engagement_score=?, behavioral_tags=?, metadata=?, tenure_days=?, updated_at=?
                WHERE id=?
                """,
                (
                    existing["name"], existing["company"], existing["industry"],
                    existing["product_tier"], existing["engagement_score"],
                    json.dumps(existing.get("behavioral_tags", [])),
                    json.dumps(existing.get("metadata", {})),
                    existing.get("tenure_days", 0), existing["updated_at"], customer_id,
                ),
            )
        return existing

    def delete_customer(self, customer_id: str) -> bool:
        with get_db() as conn:
            cur = conn.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
            return cur.rowcount > 0

    # ── Tickets ────────────────────────────────────────────────────────────

    def create_ticket(self, data: dict[str, Any]) -> dict[str, Any]:
        ticket_id = data.get("id") or f"TKT-{uuid.uuid4().hex[:8].upper()}"
        ts = now_iso()
        category = data.get("category") or "general"
        priority = data.get("priority") or "medium"
        assigned = data.get("assigned_agent") or self._route_agent(category, priority)
        record = {
            "id": ticket_id,
            "customer_id": data["customer_id"],
            "title": data["title"],
            "description": data.get("description", ""),
            "category": category,
            "priority": priority,
            "status": "Open",
            "assigned_agent": assigned,
            "ai_assisted": int(data.get("ai_assisted", False)),
            "csat_score": data.get("csat_score"),
            "created_at": ts,
            "updated_at": ts,
            "resolved_at": None,
        }
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO tickets
                (id, customer_id, title, description, category, priority, status,
                 assigned_agent, ai_assisted, csat_score, created_at, updated_at, resolved_at)
                VALUES (:id, :customer_id, :title, :description, :category, :priority,
                        :status, :assigned_agent, :ai_assisted, :csat_score,
                        :created_at, :updated_at, :resolved_at)
                """,
                record,
            )
            conn.execute(
                "UPDATE customers SET ticket_count = ticket_count + 1, updated_at = ? WHERE id = ?",
                (ts, data["customer_id"]),
            )
        self.log_interaction(
            customer_id=data["customer_id"],
            channel="ticket",
            event_type="ticket_created",
            content=data["title"],
            ticket_id=ticket_id,
        )
        out = dict(record)
        out["ai_assisted"] = bool(out["ai_assisted"])
        return out

    def get_ticket(self, ticket_id: str) -> dict[str, Any] | None:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return row_to_dict(row)

    def list_tickets(self, customer_id: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM tickets WHERE 1=1"
        params: list[Any] = []
        if customer_id:
            query += " AND customer_id = ?"
            params.append(customer_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        with get_db() as conn:
            rows = conn.execute(query, params).fetchall()
        return [row_to_dict(r) for r in rows if r]

    def update_ticket_status(self, ticket_id: str, new_status: str) -> dict[str, Any] | None:
        if new_status not in TICKET_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            return None
        current = ticket["status"]
        if new_status not in VALID_TRANSITIONS.get(current, set()) and new_status != current:
            raise ValueError(f"Cannot transition from {current} to {new_status}")
        ts = now_iso()
        resolved_at = ts if new_status in ("Resolved", "Closed") else ticket.get("resolved_at")
        with get_db() as conn:
            conn.execute(
                "UPDATE tickets SET status=?, updated_at=?, resolved_at=? WHERE id=?",
                (new_status, ts, resolved_at, ticket_id),
            )
        ticket["status"] = new_status
        ticket["updated_at"] = ts
        ticket["resolved_at"] = resolved_at
        return ticket

    # ── Interactions & timeline ────────────────────────────────────────────

    def log_interaction(
        self,
        customer_id: str,
        channel: str,
        event_type: str,
        content: str,
        ticket_id: str | None = None,
        duration_minutes: float = 0.0,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        interaction_id = f"INT-{uuid.uuid4().hex[:8].upper()}"
        ts = timestamp or now_iso()
        record = {
            "id": interaction_id,
            "customer_id": customer_id,
            "channel": channel,
            "event_type": event_type,
            "content": content,
            "ticket_id": ticket_id,
            "duration_minutes": duration_minutes,
            "timestamp": ts,
        }
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO interactions
                (id, customer_id, channel, event_type, content, ticket_id, duration_minutes, timestamp)
                VALUES (:id, :customer_id, :channel, :event_type, :content, :ticket_id,
                        :duration_minutes, :timestamp)
                """,
                record,
            )
        return record

    def get_timeline(self, customer_id: str) -> list[dict[str, Any]]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM interactions WHERE customer_id = ? ORDER BY timestamp ASC",
                (customer_id,),
            ).fetchall()
        return [row_to_dict(r) for r in rows if r]

    # ── Segmentation ───────────────────────────────────────────────────────

    def segment_customers(self, rules: dict[str, Any] | None = None) -> dict[str, list[str]]:
        rules = rules or {}
        min_engagement = float(rules.get("min_engagement", 0))
        max_tickets = int(rules.get("max_ticket_frequency", 9999))
        industries = rules.get("industries")
        min_tenure = int(rules.get("min_tenure_days", 0))

        segments: dict[str, list[str]] = {
            "high_value": [],
            "at_risk": [],
            "new": [],
            "standard": [],
        }
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM customers").fetchall()
        for row in rows:
            c = row_to_dict(row)
            if not c:
                continue
            if industries and c.get("industry") not in industries:
                continue
            if c.get("tenure_days", 0) < min_tenure:
                continue
            eng = c.get("engagement_score", 0)
            tickets = c.get("ticket_count", 0)
            if eng >= 75 and tickets <= max_tickets:
                segments["high_value"].append(c["id"])
            elif eng < 40 or tickets > 10:
                segments["at_risk"].append(c["id"])
            elif c.get("tenure_days", 0) < 90:
                segments["new"].append(c["id"])
            elif eng >= min_engagement:
                segments["standard"].append(c["id"])
            else:
                segments["at_risk"].append(c["id"])
        return segments

    # ── Bulk ingestion ─────────────────────────────────────────────────────

    def bulk_ingest(self, payload: dict[str, Any]) -> dict[str, int]:
        customers = payload.get("customers", [])
        tickets = payload.get("tickets", [])
        interactions = payload.get("interactions", [])
        seen_emails: set[str] = set()
        stats = {"customers": 0, "tickets": 0, "interactions": 0, "skipped": 0}

        with get_db() as conn:
            for c in customers:
                email = c.get("email", "")
                if not email or email in seen_emails:
                    stats["skipped"] += 1
                    continue
                existing = conn.execute("SELECT id FROM customers WHERE email = ?", (email,)).fetchone()
                if existing:
                    stats["skipped"] += 1
                    continue
                seen_emails.add(email)
                self.create_customer(c)
                stats["customers"] += 1

        seen_tickets: set[str] = set()
        for t in tickets:
            tid = t.get("id") or f"TKT-{uuid.uuid4().hex[:8].upper()}"
            if tid in seen_tickets:
                stats["skipped"] += 1
                continue
            if not self.get_customer(t["customer_id"]):
                stats["skipped"] += 1
                continue
            seen_tickets.add(tid)
            ts = t.get("created_at") or now_iso()
            record = {
                "id": tid,
                "customer_id": t["customer_id"],
                "title": t["title"],
                "description": t.get("description", ""),
                "category": t.get("category", "general"),
                "priority": t.get("priority", "medium"),
                "status": t.get("status", "Open"),
                "assigned_agent": t.get("assigned_agent") or self._route_agent(t.get("category", "general"), t.get("priority", "medium")),
                "ai_assisted": int(t.get("ai_assisted", False)),
                "csat_score": t.get("csat_score"),
                "created_at": ts,
                "updated_at": t.get("updated_at") or ts,
                "resolved_at": t.get("resolved_at"),
            }
            with get_db() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO tickets
                    (id, customer_id, title, description, category, priority, status,
                     assigned_agent, ai_assisted, csat_score, created_at, updated_at, resolved_at)
                    VALUES (:id, :customer_id, :title, :description, :category, :priority,
                            :status, :assigned_agent, :ai_assisted, :csat_score,
                            :created_at, :updated_at, :resolved_at)
                    """,
                    record,
                )
            stats["tickets"] += 1

        for i in interactions:
            if not self.get_customer(i["customer_id"]):
                stats["skipped"] += 1
                continue
            self.log_interaction(
                customer_id=i["customer_id"],
                channel=i.get("channel", "portal"),
                event_type=i.get("event_type", "note"),
                content=i.get("content", ""),
                ticket_id=i.get("ticket_id"),
                duration_minutes=float(i.get("duration_minutes", 0)),
                timestamp=i.get("timestamp"),
            )
            stats["interactions"] += 1

        return stats

    def _assign_cohort(self, data: dict[str, Any]) -> str:
        acq = (data.get("acquisition_date") or now_iso()[:10])[:7]
        industry = data.get("industry", "SaaS")
        tier = data.get("product_tier", "Starter")
        return f"{acq}_{industry}_{tier}".replace(" ", "_")

    def _route_agent(self, category: str, priority: str) -> str:
        pool = {
            "billing": "AGT-BILL-01",
            "technical": "AGT-TECH-01",
            "account": "AGT-ACC-01",
            "general": "AGT-GEN-01",
        }
        if priority == "critical":
            return "AGT-ESC-01"
        return pool.get(category, "AGT-GEN-01")


crm_service = CRMService()


def main() -> None:
    """Standalone CRM module demo."""
    c = crm_service.create_customer({
        "name": "Demo User",
        "email": "demo@ecell.test",
        "industry": "SaaS",
        "product_tier": "Growth",
        "engagement_score": 72,
    })
    print("Created customer:", c["id"], c.get("cohort_id"))
    t = crm_service.create_ticket({
        "customer_id": c["id"],
        "title": "Demo ticket",
        "description": "Module 1 standalone test",
        "category": "technical",
    })
    print("Created ticket:", t["id"], t["status"])
    print("Segments:", crm_service.segment_customers())


if __name__ == "__main__":
    main()
