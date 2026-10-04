from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR, STATE_FILE


def ensure_storage() -> Path:
    root = Path(__file__).resolve().parent.parent
    data_dir = root / DATA_DIR
    data_dir.mkdir(exist_ok=True)
    return data_dir / STATE_FILE


def load_state() -> dict[str, Any]:
    file_path = ensure_storage()
    if not file_path.exists():
        return {"agents": [], "tasks": [], "metrics": {"created_agents": 0, "completed_tasks": 0}}

    try:
        with file_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return {"agents": [], "tasks": [], "metrics": {"created_agents": 0, "completed_tasks": 0}}
        return data
    except json.JSONDecodeError:
        return {"agents": [], "tasks": [], "metrics": {"created_agents": 0, "completed_tasks": 0}}


def save_state(state: dict[str, Any]) -> None:
    file_path = ensure_storage()
    with file_path.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
