from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List


@dataclass
class Agent:
    id: str
    name: str
    agent_type: str
    description: str
    capabilities: List[str] = field(default_factory=list)
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
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "memory": self.memory,
        }

    def respond(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "who created you" in lowered or "who made you" in lowered:
            return "Abhishek a professional software eng"

        if self.agent_type == "ai":
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
