"""
Module 2 — Per-customer interaction memory (short-term + long-term layers).
"""

from __future__ import annotations

import json
from typing import Any

from src.database import get_db, now_iso, row_to_dict
from src.llm import llm_client

SHORT_TERM_LIMIT = 20


class MemoryService:
    """Persistent per-customer memory buffers with compression into long-term store."""

    def get_memory(self, customer_id: str) -> dict[str, Any]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM customer_memory WHERE customer_id = ?", (customer_id,)
            ).fetchone()
        if not row:
            return {"customer_id": customer_id, "short_term": [], "long_term": ""}
        data = row_to_dict(row)
        if data:
            try:
                data["short_term"] = json.loads(data.get("short_term", "[]"))
            except json.JSONDecodeError:
                data["short_term"] = []
        return data or {"customer_id": customer_id, "short_term": [], "long_term": ""}

    def append_short_term(self, customer_id: str, role: str, content: str) -> dict[str, Any]:
        memory = self.get_memory(customer_id)
        short_term: list[dict] = memory.get("short_term", [])
        short_term.append({"role": role, "content": content, "timestamp": now_iso()})
        if len(short_term) > SHORT_TERM_LIMIT:
            overflow = short_term[: len(short_term) - SHORT_TERM_LIMIT + 5]
            short_term = short_term[-SHORT_TERM_LIMIT:]
            self._compress_to_long_term(customer_id, memory.get("long_term", ""), overflow)
            memory = self.get_memory(customer_id)
        self._persist(customer_id, short_term, memory.get("long_term", ""))
        return self.get_memory(customer_id)

    def retrieve_context(self, customer_id: str, query: str, max_turns: int = 8) -> str:
        memory = self.get_memory(customer_id)
        short_term = memory.get("short_term", [])[-max_turns:]
        parts = []
        if memory.get("long_term"):
            parts.append(f"Long-term summary: {memory['long_term']}")
        for turn in short_term:
            parts.append(f"{turn['role']}: {turn['content']}")
        parts.append(f"Current query: {query}")
        return "\n".join(parts)

    def cross_session_history(self, customer_id: str, limit: int = 50) -> list[dict[str, Any]]:
        memory = self.get_memory(customer_id)
        return memory.get("short_term", [])[-limit:]

    def _compress_to_long_term(self, customer_id: str, existing: str, turns: list[dict]) -> None:
        transcript = "\n".join(f"{t['role']}: {t['content']}" for t in turns)
        prompt = (
            f"Compress this customer support conversation into 3-5 bullet points for long-term memory.\n"
            f"Existing memory: {existing or 'None'}\n\nConversation:\n{transcript}"
        )
        result = llm_client.invoke(prompt, system="You summarize CRM interactions concisely.")
        long_term = result["text"]
        memory = self.get_memory(customer_id)
        self._persist(customer_id, memory.get("short_term", []), long_term)

    def _persist(self, customer_id: str, short_term: list, long_term: str) -> None:
        ts = now_iso()
        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO customer_memory (customer_id, short_term, long_term, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    short_term=excluded.short_term,
                    long_term=excluded.long_term,
                    updated_at=excluded.updated_at
                """,
                (customer_id, json.dumps(short_term), long_term, ts),
            )


memory_service = MemoryService()


def main() -> None:
    from src.crm import crm_service

    customers = crm_service.list_customers(limit=1)
    if not customers:
        print("No customers — run run_pipeline.py first")
        return
    cid = customers[0]["id"]
    memory_service.append_short_term(cid, "user", "Hello, I need help with billing")
    ctx = memory_service.retrieve_context(cid, "Follow up on my invoice")
    print("Context preview:", ctx[:300])


if __name__ == "__main__":
    main()
