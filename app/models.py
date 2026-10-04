from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List

from app.config import DEFAULT_IDENTITY
from app.llm import LLMClient


@dataclass
class Agent:
    id: str
    name: str
    agent_type: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    provider: str = "local"
    model: str | None = None
    system_prompt: str = "You are a helpful Hugo agent."
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    memory: List[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.agent_type,
            "description": self.description,
            "capabilities": self.capabilities,
            "provider": self.provider,
            "model": self.model,
            "system_prompt": self.system_prompt,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "memory": self.memory,
        }

    def respond(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "who created you" in lowered or "who made you" in lowered:
            return DEFAULT_IDENTITY

        if self.provider != "local" and self.model:
            response = LLMClient(self.provider, self.model).generate(prompt, self.system_prompt)
            self.memory.append(prompt)
            return response

        if self.agent_type in {"ai", "ai-openai", "ai-claude", "ai-gemini"}:
            result = f"[{self.name}] AI agent processed: '{prompt}'"
        else:
            result = f"[{self.name}] Task agent completed the task: '{prompt}'"

        self.memory.append(prompt)
        return result


@dataclass
class Task:
    id: str
    description: str
    status: str
    assigned_agent: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "assigned_agent": self.assigned_agent,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
