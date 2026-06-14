"""Unified LLM narration facade.

Preference order for every call: OpenRouter (``OPENROUTER_API_KEY``) → legacy
direct Anthropic (``ANTHROPIC_API_KEY``) → ``None`` (callers then use
deterministic, template-based narration). The whole app runs with no keys at
all; keys only upgrade prose from templated to conversational.
"""
from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from typing import Optional

from src.core.config import settings
from src.core.logger import logger
from src.llm import openrouter


@lru_cache(maxsize=1)
def _anthropic():
    """Legacy direct-Anthropic client (used only if OpenRouter is absent)."""
    if not settings.ANTHROPIC_API_KEY.strip():
        return None
    try:
        import anthropic

        return anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Anthropic client unavailable (%s).", exc)
        return None


def available() -> bool:
    return openrouter.enabled() or _anthropic() is not None


def _anthropic_narrate(system: str, prompt: str, max_tokens: int) -> Optional[str]:
    client = _anthropic()
    if client is None:
        return None
    try:
        model = settings.COACH_MODEL.split("/")[-1]  # strip "anthropic/" prefix if present
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = stream.get_final_message()
        return "".join(b.text for b in message.content if b.type == "text").strip() or None
    except Exception as exc:  # pragma: no cover - network/runtime
        logger.warning("Anthropic narration failed (%s).", exc)
        return None


def narrate(system: str, prompt: str, max_tokens: int = 1200) -> Optional[str]:
    """Generate coaching prose from a structured prompt, or None to fall back."""
    text = openrouter.chat(
        [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    if text:
        return text
    return _anthropic_narrate(system, prompt, max_tokens)


def narrate_with_history(
    system: str, history: list[dict], prompt: str, max_tokens: int = 1000
) -> Optional[str]:
    """Like ``narrate`` but threads prior conversation turns (memory)."""
    messages = [{"role": "system", "content": system}, *history, {"role": "user", "content": prompt}]
    text = openrouter.chat(messages, max_tokens=max_tokens)
    if text:
        return text
    folded = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    return _anthropic_narrate(system, (folded + "\n\n" + prompt).strip(), max_tokens)


def stream_narrate(
    system: str, history: Optional[list[dict]], prompt: str, max_tokens: int = 1000
) -> Iterator[str]:
    """Stream coaching prose token-by-token (OpenRouter only)."""
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})
    yield from openrouter.stream_chat(messages, max_tokens=max_tokens)
