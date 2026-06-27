"""
Module 2 — LangChain summarization chains and LangGraph agent workflows.
"""

from __future__ import annotations

import re
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from src.crm import crm_service
from src.llm import llm_client
from src.memory import memory_service

SUMMARIZE_SYSTEM = (
    "You are an enterprise CRM assistant. Summarize support tickets with: "
    "key issues, urgency (low/medium/high/critical), and suggested resolution path. "
    "Cite only facts present in the ticket. If uncertain, say so."
)

AGENT_SYSTEM = (
    "You are E-Cell CRM AI agent. Answer using ONLY provided customer context and ticket data. "
    "Include source references (ticket IDs, interaction types). Never invent account details."
)


class AgentState(TypedDict, total=False):
    customer_id: str
    query: str
    context: str
    ticket_data: str
    route_category: str
    priority: str
    draft_response: str
    sources: list[str]
    confidence: float
    escalated: bool
    hallucination_flags: list[str]


def _extract_sources(text: str, ticket_ids: list[str]) -> list[str]:
    sources = []
    for tid in ticket_ids:
        if tid in text:
            sources.append(tid)
    return sources or ticket_ids[:3]


def _hallucination_guard(response: str, context: str, ticket_ids: list[str]) -> tuple[float, list[str]]:
    flags: list[str] = []
    confidence = 0.85

    # Penalize if response mentions specific dollar amounts not in context
    amounts = re.findall(r"\$[\d,]+(?:\.\d{2})?", response)
    for amt in amounts:
        if amt not in context:
            flags.append(f"unsourced_amount:{amt}")
            confidence -= 0.15

    # Require at least one verifiable ticket reference when tickets exist
    if ticket_ids and not any(tid in response for tid in ticket_ids):
        flags.append("missing_ticket_citation")
        confidence -= 0.1

    # Detect overconfident claims
    if any(p in response.lower() for p in ("guaranteed", "100%", "definitely resolved")):
        flags.append("overconfident_language")
        confidence -= 0.05

    confidence = max(0.3, min(1.0, confidence))
    return confidence, flags


class TicketSummarizationChain:
    """LangChain-style summarization pipeline for tickets."""

    def summarize(self, ticket_id: str, tone: str = "professional", max_length: str = "medium") -> dict[str, Any]:
        ticket = crm_service.get_ticket(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket not found: {ticket_id}")

        customer = crm_service.get_customer(ticket["customer_id"])
        prompt = (
            f"Summarize this support ticket.\n"
            f"Tone: {tone}. Length: {max_length}.\n"
            f"Ticket ID: {ticket_id}\n"
            f"Title: {ticket['title']}\n"
            f"Description: {ticket['description']}\n"
            f"Category: {ticket['category']}, Priority: {ticket['priority']}, Status: {ticket['status']}\n"
            f"Customer: {customer.get('name') if customer else 'Unknown'} ({ticket['customer_id']})\n"
        )
        result = llm_client.invoke(prompt, system=SUMMARIZE_SYSTEM)

        key_issues = []
        for line in result["text"].split("."):
            if any(k in line.lower() for k in ("issue", "problem", "error", "billing", "bug")):
                key_issues.append(line.strip())

        suggested = (
            f"Acknowledge {ticket['category']} concern, verify account status, "
            f"target resolution within SLA for {ticket['priority']} priority."
        )

        return {
            "ticket_id": ticket_id,
            "summary": result["text"],
            "key_issues": key_issues[:5] or [ticket["title"]],
            "urgency": ticket["priority"],
            "suggested_response": suggested,
            "source": ticket_id,
            "confidence": result["confidence"],
            "latency_ms": result["latency_ms"],
        }


def _node_load_context(state: AgentState) -> AgentState:
    customer_id = state["customer_id"]
    memory_ctx = memory_service.retrieve_context(customer_id, state["query"])
    tickets = crm_service.list_tickets(customer_id=customer_id)
    ticket_lines = [
        f"{t['id']}: {t['title']} [{t['status']}] — {t['description'][:200]}"
        for t in tickets[:5]
    ]
    state["ticket_data"] = "\n".join(ticket_lines)
    state["context"] = f"{memory_ctx}\n\nOpen tickets:\n{state['ticket_data']}"
    return state


def _node_route_ticket(state: AgentState) -> AgentState:
    prompt = f"Classify category for query: {state['query']}\nContext:\n{state['context'][:1500]}"
    result = llm_client.invoke(prompt, system="Return one word: billing, technical, account, or general.")
    category = result["text"].strip().lower().split()[0] if result["text"] else "general"
    if category not in ("billing", "technical", "account", "general"):
        category = "general"
    state["route_category"] = category
    state["priority"] = "high" if "urgent" in state["query"].lower() else "medium"
    return state


def _node_generate_response(state: AgentState) -> AgentState:
    prompt = (
        f"Customer query: {state['query']}\n\n"
        f"Context:\n{state['context']}\n\n"
        f"Route: {state.get('route_category')} / {state.get('priority')}\n"
        "Draft a helpful agent reply with ticket ID citations where applicable."
    )
    result = llm_client.invoke(prompt, system=AGENT_SYSTEM)
    ticket_ids = re.findall(r"TKT-[A-F0-9]{8}", state.get("ticket_data", ""))
    confidence, flags = _hallucination_guard(result["text"], state["context"], ticket_ids)
    state["draft_response"] = result["text"]
    state["sources"] = _extract_sources(result["text"], ticket_ids)
    state["confidence"] = confidence
    state["hallucination_flags"] = flags
    return state


def _node_escalation_check(state: AgentState) -> AgentState:
    escalated = (
        state.get("priority") == "high"
        and state.get("confidence", 1.0) < 0.6
    ) or "escalat" in state["query"].lower()
    state["escalated"] = escalated
    if escalated:
        state["draft_response"] += "\n\n[Escalated to supervisor per low-confidence / urgent policy]"
    return state


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("load_context", _node_load_context)
    graph.add_node("route", _node_route_ticket)
    graph.add_node("generate", _node_generate_response)
    graph.add_node("escalation", _node_escalation_check)

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "route")
    graph.add_edge("route", "generate")
    graph.add_edge("generate", "escalation")
    graph.add_edge("escalation", END)
    return graph.compile()


class AgentWorkflow:
    def __init__(self) -> None:
        self.graph = build_agent_graph()
        self.summarizer = TicketSummarizationChain()

    def query_agent(self, customer_id: str, query: str, agent_id: str = "AI-AGENT-01") -> dict[str, Any]:
        memory_service.append_short_term(customer_id, "user", query)
        initial: AgentState = {"customer_id": customer_id, "query": query}
        final = self.graph.invoke(initial)
        answer = final.get("draft_response", "")
        memory_service.append_short_term(customer_id, "assistant", answer)

        return {
            "answer": answer,
            "source": final.get("sources", []),
            "confidence": final.get("confidence", 0.7),
            "agent_id": agent_id,
            "route_category": final.get("route_category"),
            "priority": final.get("priority"),
            "escalated": final.get("escalated", False),
            "hallucination_flags": final.get("hallucination_flags", []),
        }

    def summarize_ticket(self, ticket_id: str, **kwargs: Any) -> dict[str, Any]:
        return self.summarizer.summarize(ticket_id, **kwargs)


agent_workflow = AgentWorkflow()


def main() -> None:
    from src.crm import crm_service

    customers = crm_service.list_customers(limit=1)
    if not customers:
        print("No customers — run run_pipeline.py first")
        return
    cid = customers[0]["id"]
    result = agent_workflow.query_agent(cid, "What open issues do I have?")
    print("Agent answer:", result["answer"][:200])
    print("Confidence:", result["confidence"])


if __name__ == "__main__":
    main()
