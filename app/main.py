from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.models import Agent, Task
from app.state_store import load_state, save_state


class AgentFactory:
    def __init__(self) -> None:
        self.state = load_state()
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self._hydrate()

    def _hydrate(self) -> None:
        for raw in self.state.get("agents", []):
            agent = Agent(**raw)
            self.agents[agent.id] = agent

        for raw in self.state.get("tasks", []):
            task = Task(**raw)
            self.tasks[task.id] = task

    def _persist(self) -> None:
        self.state["agents"] = [agent.to_dict() for agent in self.agents.values()]
        self.state["tasks"] = [task.to_dict() for task in self.tasks.values()]
        save_state(self.state)

    def create_agent(self, name: str, agent_type: str, description: str, capabilities: list[str] | None = None) -> Agent:
        agent_id = str(uuid.uuid4())[:8]
        agent = Agent(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            description=description,
            capabilities=capabilities or [],
            created_at=datetime.now(timezone.utc),
        )
        self.agents[agent_id] = agent
        self.state["metrics"] = self.state.get("metrics", {})
        self.state["metrics"]["created_agents"] = len(self.agents)
        self._persist()
        return agent

    def create_task(self, description: str, assigned_agent: str | None = None) -> Task:
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            description=description,
            status="queued",
            assigned_agent=assigned_agent,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.tasks[task_id] = task
        self._persist()
        return task

    def list_agents(self) -> list[Agent]:
        return list(self.agents.values())

    def list_tasks(self) -> list[Task]:
        return list(self.tasks.values())

    def process_task(self, task_id: str) -> Task:
        task = self.tasks.get(task_id)
        if task is None:
            raise ValueError("Task not found")

        task.status = "in_progress"
        task.updated_at = datetime.now(timezone.utc)
        self._persist()

        target = self.agents.get(task.assigned_agent) if task.assigned_agent else next(iter(self.agents.values()), None)
        if target is not None:
            target.respond(task.description)

        task.status = "completed"
        task.updated_at = datetime.now(timezone.utc)
        self.state["metrics"] = self.state.get("metrics", {})
        self.state["metrics"]["completed_tasks"] = sum(1 for t in self.tasks.values() if t.status == "completed")
        self._persist()
        return task

    def send_message(self, agent_id: str, prompt: str) -> str:
        agent = self.agents.get(agent_id)
        if agent is None:
            raise ValueError("Agent not found")
        response = agent.respond(prompt)
        self._persist()
        return response

    def metrics(self) -> dict[str, Any]:
        return {
            "agents": len(self.agents),
            "tasks": len(self.tasks),
            "completed_tasks": sum(1 for task in self.tasks.values() if task.status == "completed"),
            "queued_tasks": sum(1 for task in self.tasks.values() if task.status == "queued"),
            "in_progress_tasks": sum(1 for task in self.tasks.values() if task.status == "in_progress"),
        }
