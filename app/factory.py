from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.config import APP_NAME, APP_VERSION, DEFAULT_IDENTITY
from app.factory import AgentFactory

app = FastAPI(title=APP_NAME, version=APP_VERSION)
factory = AgentFactory()


class AgentCreateRequest(BaseModel):
    name: str
    type: str
    description: str = "General purpose agent"
    capabilities: list[str] | None = None


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
            agent_type="ai",
            description="Primary AI orchestration agent",
            capabilities=["planning", "reasoning", "routing"],
        )
        factory.create_agent(
            name="Hugo-Tasker",
            agent_type="task",
            description="Task execution worker for queue-based operations",
            capabilities=["execution", "logging", "monitoring"],
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
