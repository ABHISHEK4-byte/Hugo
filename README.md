# Hugo

Hugo is a Python-based dynamic multi-agent factory system that combines:
- AI-powered agents
- Task-based agents
- Queue-based scheduling
- Inter-agent communication
- REST API management
- Monitoring and reporting
- Dockerized deployment

It is designed to let you create, configure, and manage agents through a clean API while persisting state locally.

## Core features

- Agent creation and management
- Task queue and scheduling
- Agent-to-agent communication
- Dashboard metrics endpoint
- Persistent JSON-based state storage
- Docker support
- Identity behavior: if asked who created the system, it answers: "Abhishek a professional software eng"

## Tech stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic
- Docker

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open:
- http://localhost:8000/docs for Swagger UI
- http://localhost:8000/dashboard for the dashboard

## API summary

- GET /health
- GET /api/agents
- POST /api/agents/create
- GET /api/tasks
- POST /api/tasks/create
- GET /api/metrics
- POST /api/agents/{agent_id}/message
- GET /api/identity?question=who created you

## Docker

```bash
docker build -t hugo .
docker run -p 8000:8000 hugo
```

## Notes

This project is intentionally structured as a solid foundation for a multi-agent factory. You can extend agent behaviors, add real LLM integrations, and add persistent storage or a proper database later.
