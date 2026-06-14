"""OpenRouter client (OpenAI-compatible chat completions).

One place for every LLM call: narration, agent routing, transaction
categorization, and token-by-token streaming. Every function degrades to
``None`` / empty so callers fall back to deterministic logic when
``OPENROUTER_API_KEY`` is unset or the network/API misbehaves.
"""
from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Optional

from src.core.config import settings
from src.core.logger import logger


def enabled() -> bool:
    return settings.openrouter_enabled


def _model_id(model: Optional[str]) -> str:
    """Resolve to an OpenRouter slug, which must be provider-prefixed.

    A bare Anthropic id (e.g. ``claude-opus-4-8``) is a 400 on OpenRouter, so
    prefix ``anthropic/`` when a known-Anthropic name arrives without a slash.
    """
    name = model or settings.COACH_MODEL
    if "/" not in name and name.startswith("claude-"):
        return f"anthropic/{name}"
    return name


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        # Optional attribution headers OpenRouter recommends.
        "HTTP-Referer": settings.FRONTEND_URL,
        "X-Title": settings.APP_NAME,
    }


def chat(
    messages: list[dict],
    model: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.4,
    response_json: bool = False,
) -> Optional[str]:
    """Blocking chat completion. Returns the assistant text, or None on failure."""
    if not enabled():
        return None
    try:
        import httpx

        payload: dict = {
            "model": _model_id(model),
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_json:
            payload["response_format"] = {"type": "json_object"}
        resp = httpx.post(
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        return (resp.json()["choices"][0]["message"]["content"] or "").strip() or None
    except Exception as exc:  # pragma: no cover - network/runtime
        logger.warning("OpenRouter chat failed (%s); falling back.", exc)
        return None


def stream_chat(
    messages: list[dict],
    model: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.4,
) -> Iterator[str]:
    """Yield text deltas as they arrive (SSE). Empty generator on failure."""
    if not enabled():
        return
    try:
        import httpx

        with httpx.stream(
            "POST",
            f"{settings.OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json={
                "model": _model_id(model),
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
            timeout=120,
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    delta = json.loads(data)["choices"][0]["delta"].get("content")
                    if delta:
                        yield delta
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    except Exception as exc:  # pragma: no cover - network/runtime
        logger.warning("OpenRouter stream failed (%s).", exc)
        return


def route_agents(query: str, available: list[str]) -> Optional[list[str]]:
    """Ask the LLM which specialist agents are relevant to a query."""
    system = (
        "You are a router for a multi-agent financial coach. Given a user "
        "request, choose which specialist agents should handle it. "
        f"Available agents: {', '.join(available)}. "
        "Respond ONLY with JSON: {\"agents\": [\"name\", ...]}. "
        "Pick the minimal relevant set; if the request is broad/unclear, "
        "include all agents."
    )
    out = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": query}],
        model=settings.ROUTER_MODEL,
        max_tokens=120,
        temperature=0.0,
        response_json=True,
    )
    if not out:
        return None
    try:
        names = json.loads(out).get("agents", [])
        picked = [n for n in names if n in available]
        return picked or None
    except (json.JSONDecodeError, AttributeError):
        return None


def categorize_transactions(descriptions: list[str], categories: list[str]) -> Optional[dict]:
    """Map each transaction description to one of ``categories``.

    Returns ``{description: category}``; None on failure.
    """
    system = (
        "You categorize bank/credit-card transactions for an Indian user. "
        f"Assign each description to EXACTLY ONE of these categories: {', '.join(categories)}. "
        "Respond ONLY with JSON mapping each input description to its category, "
        "e.g. {\"SWIGGY ORDER\": \"food\"}."
    )
    user = "Categorize these descriptions:\n" + "\n".join(f"- {d}" for d in descriptions)
    out = chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model=settings.ROUTER_MODEL,
        max_tokens=800,
        temperature=0.0,
        response_json=True,
    )
    if not out:
        return None
    try:
        mapping = json.loads(out)
        return {k: v for k, v in mapping.items() if v in categories}
    except (json.JSONDecodeError, AttributeError):
        return None
