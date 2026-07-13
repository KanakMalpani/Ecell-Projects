"""
Generate synthetic CRM dataset using Faker + optional LLM enhancement.

WHAT THIS FILE DOES
-------------------
Creates the full demo dataset saved to data/synthetic_crm_dataset.json:
  - 520 customers across 6 industries × 3 product tiers
  - 1050 tickets with realistic titles, statuses, CSAT scores
  - 2500 interactions (email, chat, call, portal) over ~6 months

GENERATION STRATEGY
-------------------
  Customers: Faker names/companies, random engagement 15-95, tenure from acq date
  Tickets:   First 20 descriptions LLM-enhanced; rest use templates (speed)
  Interactions: 40% linked to a ticket; random channel and event type
  Seeded: random.seed(42) + Faker.seed(42) for reproducibility

RUN
---
  python scripts/generate_data.py
  (or via: python run_pipeline.py)
"""

from __future__ import annotations

import json
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from faker import Faker

from src.config import DATA_DIR
from src.crm import INDUSTRIES, PRODUCT_TIERS
from src.llm import llm_client

fake = Faker()
Faker.seed(42)
random.seed(42)

CATEGORIES = ("billing", "technical", "account", "general")
PRIORITIES = ("low", "medium", "high", "critical")
CHANNELS = ("email", "chat", "call", "ticket", "portal")
TITLES = {
    "billing": ["Invoice mismatch", "Refund request", "Payment failed", "Subscription upgrade issue"],
    "technical": ["API timeout errors", "Login failure", "Integration broken", "Dashboard not loading"],
    "account": ["User access request", "Plan downgrade", "Account merge", "SSO configuration"],
    "general": ["Product question", "Feature request", "Onboarding help", "Documentation unclear"],
}


def _random_date(start: datetime, end: datetime) -> str:
    delta = end - start
    day = start + timedelta(days=random.randint(0, max(delta.days, 1)))
    return day.isoformat() + "Z"


def generate_customers(n: int = 520) -> list[dict]:
    customers = []
    start = datetime.utcnow() - timedelta(days=210)
    end = datetime.utcnow() - timedelta(days=7)
    for i in range(n):
        acq = _random_date(start, end)
        acq_dt = datetime.fromisoformat(acq.replace("Z", ""))
        tenure = (datetime.utcnow() - acq_dt).days
        industry = random.choice(INDUSTRIES)
        tier = random.choices(PRODUCT_TIERS, weights=[0.4, 0.35, 0.25])[0]
        engagement = round(random.uniform(15, 95), 1)
        tags = random.sample(["power_user", "trial", "enterprise", "self_serve", "at_risk"], k=random.randint(0, 2))
        customers.append({
            "id": f"CUST-{uuid.uuid4().hex[:8].upper()}",
            "name": fake.name(),
            "email": f"customer{i+1}@{fake.domain_name()}",
            "company": fake.company(),
            "industry": industry,
            "product_tier": tier,
            "acquisition_date": acq[:10],
            "tenure_days": tenure,
            "engagement_score": engagement,
            "ticket_count": 0,
            "behavioral_tags": tags,
            "metadata": {"region": fake.country_code(), "seats": random.randint(1, 500)},
        })
    return customers


def _llm_ticket_description(title: str, category: str) -> str:
    prompt = f"Write a 2-sentence realistic B2B SaaS support ticket description.\nTitle: {title}\nCategory: {category}"
    result = llm_client.invoke(prompt, system="Be concise and realistic.")
    return result["text"][:500]


def generate_tickets(customers: list[dict], n: int = 1050) -> list[dict]:
    tickets = []
    start = datetime.utcnow() - timedelta(days=180)
    end = datetime.utcnow()
    statuses = ["Open", "In Progress", "Escalated", "Resolved", "Closed"]
    weights = [0.12, 0.15, 0.08, 0.35, 0.30]

    for i in range(n):
        cust = random.choice(customers)
        category = random.choice(CATEGORIES)
        title = random.choice(TITLES[category])
        created = _random_date(start, end)
        status = random.choices(statuses, weights=weights)[0]
        resolved_at = None
        if status in ("Resolved", "Closed"):
            c_dt = datetime.fromisoformat(created.replace("Z", ""))
            resolved_at = (c_dt + timedelta(hours=random.randint(2, 120))).isoformat() + "Z"

        use_llm = i < 20  # LLM-enhance first batch; rest use templates for speed
        if use_llm:
            desc = _llm_ticket_description(title, category)
        else:
            desc = f"Customer reports: {title.lower()}. Impact on daily operations. Requesting assistance per SLA."

        tickets.append({
            "id": f"TKT-{uuid.uuid4().hex[:8].upper()}",
            "customer_id": cust["id"],
            "title": title,
            "description": desc,
            "category": category,
            "priority": random.choice(PRIORITIES),
            "status": status,
            "assigned_agent": f"AGT-{category[:4].upper()}-01",
            "ai_assisted": random.random() < 0.35,
            "csat_score": round(random.uniform(2.5, 5.0), 1) if status in ("Resolved", "Closed") else None,
            "created_at": created,
            "updated_at": resolved_at or created,
            "resolved_at": resolved_at,
        })
    return tickets


def generate_interactions(customers: list[dict], tickets: list[dict], n: int = 2500) -> list[dict]:
    interactions = []
    start = datetime.utcnow() - timedelta(days=185)
    end = datetime.utcnow()
    ticket_by_cust: dict[str, list] = {}
    for t in tickets:
        ticket_by_cust.setdefault(t["customer_id"], []).append(t)

    for _ in range(n):
        cust = random.choice(customers)
        channel = random.choice(CHANNELS)
        ts = _random_date(start, end)
        cust_tickets = ticket_by_cust.get(cust["id"], [])
        tid = random.choice(cust_tickets)["id"] if cust_tickets and random.random() < 0.4 else None
        interactions.append({
            "customer_id": cust["id"],
            "channel": channel,
            "event_type": random.choice(["inbound", "outbound", "note", "status_change"]),
            "content": fake.sentence(nb_words=12),
            "ticket_id": tid,
            "duration_minutes": round(random.uniform(1, 45), 1) if channel == "call" else 0,
            "timestamp": ts,
        })
    return interactions


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    print("Generating customers...")
    customers = generate_customers(520)
    print("Generating tickets...")
    tickets = generate_tickets(customers, 1050)
    print("Generating interactions...")
    interactions = generate_interactions(customers, tickets, 2500)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "customers": customers,
        "tickets": tickets,
        "interactions": interactions,
        "stats": {
            "customer_count": len(customers),
            "ticket_count": len(tickets),
            "interaction_count": len(interactions),
        },
    }

    out = DATA_DIR / "synthetic_crm_dataset.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved {out}")
    print(f"Stats: {payload['stats']}")


if __name__ == "__main__":
    main()
