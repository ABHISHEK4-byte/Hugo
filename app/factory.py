from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.config import APP_NAME, APP_VERSION, DEFAULT_IDENTITY
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
            if "type" in raw and "agent_type" not in raw:
                raw["agent_type"] = raw.pop("type")
            agent = Agent(**raw)
            self.agents[agent.id] = agent

        for raw in self.state.get("tasks", []):
            task = Task(**raw)
            self.tasks[task.id] = task

    def _persist(self) -> None:
        self.state["agents"] = [agent.to_dict() for agent in self.agents.values()]
        self.state["tasks"] = [task.to_dict() for task in self.tasks.values()]
        save_state(self.state)

    def create_agent(
        self,
        name: str,
        agent_type: str,
        description: str,
        capabilities: list[str] | None = None,
        provider: str = "local",
        model: str | None = None,
        system_prompt: str = "You are a helpful Hugo agent.",
    ) -> Agent:
        agent_id = str(uuid.uuid4())[:8]
        agent = Agent(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            description=description,
            capabilities=capabilities or [],
            provider=provider,
            model=model,
            system_prompt=system_prompt,
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
            "providers": {
                "openai": sum(1 for agent in self.agents.values() if agent.provider == "openai"),
                "anthropic": sum(1 for agent in self.agents.values() if agent.provider == "anthropic"),
                "gemini": sum(1 for agent in self.agents.values() if agent.provider == "gemini"),
                "local": sum(1 for agent in self.agents.values() if agent.provider == "local"),
            },
        }


app = FastAPI(title=APP_NAME, version=APP_VERSION)
factory = AgentFactory()


class AgentCreateRequest(BaseModel):
    name: str
    type: str
    description: str = "General purpose agent"
    capabilities: list[str] | None = None
    provider: str = "local"
    model: str | None = None
    system_prompt: str = "You are a helpful Hugo agent."


class TaskCreateRequest(BaseModel):
    description: str
    assigned_agent: str | None = None


class MessageRequest(BaseModel):
    prompt: str


@app.on_event("startup")
def ensure_default_agents() -> None:
    if not factory.list_agents():
        factory.create_agent(
            name="Hugo-Alpha",
            agent_type="ai-openai",
            description="Primary AI orchestration agent",
            capabilities=["planning", "reasoning", "routing"],
            provider="openai",
            model="gpt-4o-mini",
            system_prompt="You are Hugo-Alpha, a high-level orchestration agent for the multi-agent factory.",
        )
        factory.create_agent(
            name="Hugo-Tasker",
            agent_type="task",
            description="Task execution worker for queue-based operations",
            capabilities=["execution", "logging", "monitoring"],
            provider="local",
        )


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "name": APP_NAME, "version": APP_VERSION}


@app.get("/api/agents")
def list_agents() -> list[dict[str, Any]]:
    return [agent.to_dict() for agent in factory.list_agents()]


@app.post("/api/agents/create")
def create_agent(request: AgentCreateRequest) -> dict[str, Any]:
    agent = factory.create_agent(
        name=request.name,
        agent_type=request.type,
        description=request.description,
        capabilities=request.capabilities or [],
        provider=request.provider,
        model=request.model,
        system_prompt=request.system_prompt,
    )
    return agent.to_dict()


@app.get("/api/tasks")
def list_tasks() -> list[dict[str, Any]]:
    return [task.to_dict() for task in factory.list_tasks()]


@app.post("/api/tasks/create")
def create_task(request: TaskCreateRequest) -> dict[str, Any]:
    task = factory.create_task(request.description, request.assigned_agent)
    return task.to_dict()


@app.post("/api/tasks/{task_id}/run")
def run_task(task_id: str) -> dict[str, Any]:
    try:
        task = factory.process_task(task_id)
        return task.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/agents/{agent_id}/message")
def agent_message(agent_id: str, request: MessageRequest) -> dict[str, str]:
    try:
        response = factory.send_message(agent_id, request.prompt)
        return {"response": response}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/metrics")
def metrics() -> dict[str, Any]:
    return factory.metrics()


@app.get("/api/identity")
def identity(question: str | None = None) -> dict[str, str]:
    question_text = (question or "").lower()
    if "who created you" in question_text or "who made you" in question_text:
        return {"answer": DEFAULT_IDENTITY}
    return {"answer": "Hugo is an autonomous multi-agent factory for task execution and orchestration."}


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return """
    <html>
      <head>
        <title>Hugo Dashboard</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 40px; background: #0f172a; color: #e2e8f0; }
          .card { background: #111827; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
          .metric { display: inline-block; margin-right: 20px; padding: 15px; border-radius: 8px; background: #1e293b; }
          pre { background: #020617; padding: 15px; border-radius: 8px; }
        </style>
      </head>
      <body>
        <h1>Hugo Control Center</h1>
        <div id="metrics" class="card"></div>
        <div class="card">
          <h3>System Overview</h3>
          <pre id="overview">Loading...</pre>
        </div>
        <script>
          async function loadMetrics() {
            const res = await fetch('/api/metrics');
            const data = await res.json();
            document.getElementById('metrics').innerHTML = `
              <div class='metric'><strong>Agents:</strong> ${data.agents}</div>
              <div class='metric'><strong>Tasks:</strong> ${data.tasks}</div>
              <div class='metric'><strong>Completed:</strong> ${data.completed_tasks}</div>
              <div class='metric'><strong>Queued:</strong> ${data.queued_tasks}</div>
            `;
            document.getElementById('overview').textContent = JSON.stringify(data, null, 2);
          }
          loadMetrics();
          setInterval(loadMetrics, 5000);
        </script>
      </body>
    </html>
    """


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "message": "Hugo is running. Use /docs for API documentation.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
