"""LLM provider abstraction — Ollama, Gemini, or deterministic mock."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from src.config import GEMINI_API_KEY, LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified interface for on-prem (Ollama) or API (Gemini) inference."""

    def __init__(self, provider: str | None = None) -> None:
        self.provider = (provider or LLM_PROVIDER).lower()

    def invoke(self, prompt: str, system: str = "", max_tokens: int = 1024) -> dict[str, Any]:
        start = time.perf_counter()
        if self.provider == "gemini" and GEMINI_API_KEY:
            text, confidence = self._gemini(prompt, system, max_tokens)
        elif self.provider == "ollama":
            text, confidence = self._ollama(prompt, system)
        else:
            text, confidence = self._mock(prompt, system)
        latency_ms = (time.perf_counter() - start) * 1000
        return {
            "text": text.strip(),
            "confidence": confidence,
            "provider": self.provider,
            "latency_ms": round(latency_ms, 2),
        }

    def _ollama(self, prompt: str, system: str) -> tuple[str, float]:
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        if system:
            payload["system"] = system
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", ""), 0.85
        except Exception as exc:
            logger.warning("Ollama unavailable (%s), falling back to mock", exc)
            return self._mock(prompt, system)

    def _gemini(self, prompt: str, system: str, max_tokens: int) -> tuple[str, float]:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=GEMINI_API_KEY,
                temperature=0.2,
                max_output_tokens=max_tokens,
            )
            messages = []
            if system:
                messages.append(("system", system))
            messages.append(("human", prompt))
            result = llm.invoke(messages)
            return str(result.content), 0.9
        except Exception as exc:
            logger.warning("Gemini unavailable (%s), falling back to mock", exc)
            return self._mock(prompt, system)

    def _mock(self, prompt: str, system: str) -> tuple[str, float]:
        """Rule-based fallback when no LLM is reachable."""
        lower = prompt.lower()
        if "summarize" in lower or "ticket" in lower:
            return (
                "Key issues: billing discrepancy and delayed response. "
                "Urgency: medium. Suggested path: verify invoice, escalate to billing team if unresolved within 24h.",
                0.72,
            )
        if "route" in lower or "category" in lower:
            if "billing" in lower:
                return "billing", 0.8
            if "technical" in lower or "bug" in lower:
                return "technical", 0.8
            return "general", 0.75
        if "churn" in lower:
            return "Churn risk moderate based on declining engagement and open ticket backlog.", 0.7
        return (
            "Based on customer history and open tickets, recommend acknowledging the issue, "
            "referencing ticket details, and offering a concrete next step within SLA.",
            0.68,
        )


llm_client = LLMClient()
