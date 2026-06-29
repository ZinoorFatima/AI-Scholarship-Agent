"""Persist and load run state as JSON under ``runs/<run_id>/state.json``."""
from __future__ import annotations

from pathlib import Path

from .config import get_settings
from .schemas import RunState


def _run_dir(run_id: str) -> Path:
    return Path(get_settings().runs_dir) / run_id


def save(state: RunState) -> Path:
    """Write a run's state to disk and return the file path."""
    path = _run_dir(state.run_id) / "state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return path


def load(run_id: str) -> RunState:
    """Load a run's state from disk."""
    path = _run_dir(run_id) / "state.json"
    if not path.exists():
        raise FileNotFoundError(f"No run found with id {run_id!r} at {path}")
    return RunState.model_validate_json(path.read_text(encoding="utf-8"))
