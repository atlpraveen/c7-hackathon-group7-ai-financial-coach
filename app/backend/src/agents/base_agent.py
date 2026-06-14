"""Base class for the specialist financial agents.

Each agent does the same two-stage job:
  1. Run deterministic financial tools over the user's profile (the "facts").
  2. Turn those facts into coaching prose — via Claude when available, or a
     built-in template otherwise.

This keeps every recommendation grounded in real numbers while still reading
like advice from a human coach.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.llm import client as llm


class BaseAgent(ABC):
    name: str = "agent"
    title: str = "Agent"

    @abstractmethod
    def analyze(self, profile: dict, params: dict | None = None) -> dict:
        """Return the structured (deterministic) analysis for this agent."""

    @abstractmethod
    def _system_prompt(self) -> str:
        ...

    @abstractmethod
    def _fallback_narrative(self, data: dict, profile: dict) -> str:
        """Deterministic prose used when no LLM is configured."""

    def narrate(self, data: dict, profile: dict) -> tuple[str, str]:
        """Return (narrative_text, generated_by)."""
        prompt = self._user_prompt(data, profile)
        text = llm.narrate(self._system_prompt(), prompt, max_tokens=900)
        if text:
            return text, "llm"
        return self._fallback_narrative(data, profile), "deterministic"

    def _user_prompt(self, data: dict, profile: dict) -> str:
        import json

        return (
            "Here is the user's financial profile and the computed analysis "
            "from our deterministic tools. Write warm, specific, actionable "
            "coaching in 2-4 short paragraphs. Reference the actual numbers. "
            "Do not invent figures beyond what is provided.\n\n"
            f"PROFILE:\n{json.dumps(profile, default=str)}\n\n"
            f"ANALYSIS:\n{json.dumps(data, default=str)}"
        )

    def run(self, profile: dict, params: dict | None = None) -> dict:
        data = self.analyze(profile, params or {})
        narrative, generated_by = self.narrate(data, profile)
        return {
            "agent": self.name,
            "title": self.title,
            "data": data,
            "narrative": narrative,
            "generated_by": generated_by,
        }
