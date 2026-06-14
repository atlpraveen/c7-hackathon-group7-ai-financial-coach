"""Inter-agent message envelope used by the orchestrator."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    sender: str
    receiver: str
    intent: str
    payload: dict = field(default_factory=dict)
