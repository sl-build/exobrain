"""Exocortex CLI — Plan state persistence in ~/.exocortex/state/plan.json."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path

STATE_DIR = Path.home() / ".exocortex" / "state"
PLAN_FILE = STATE_DIR / "plan.json"


def _plan_file(session_id: str = "") -> Path:
    if session_id:
        return STATE_DIR / f"plan-{session_id}.json"
    return PLAN_FILE


@dataclass
class PlanStep:
    title: str
    status: str  # pending | in_progress | done | blocked


@dataclass
class Plan:
    prompt: str
    steps: list[PlanStep]
    current_step: int
    created_at: float
    session_id: str = ""


def create_plan(prompt: str, step_titles: list[str], session_id: str = "") -> Plan:
    now = time.time()
    steps = []
    for i, title in enumerate(step_titles):
        status = "in_progress" if i == 0 else "pending"
        steps.append(PlanStep(title=title, status=status))
    return Plan(
        prompt=prompt,
        steps=steps,
        current_step=0,
        created_at=now,
        session_id=session_id,
    )


def load_plan(session_id: str = "") -> Plan | None:
    path = _plan_file(session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = [PlanStep(**s) for s in data["steps"]]
        return Plan(
            prompt=data["prompt"],
            steps=steps,
            current_step=data["current_step"],
            created_at=data["created_at"],
            session_id=data.get("session_id", ""),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_plan(plan: Plan) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "prompt": plan.prompt,
        "steps": [asdict(s) for s in plan.steps],
        "current_step": plan.current_step,
        "created_at": plan.created_at,
        "session_id": plan.session_id,
    }
    path = _plan_file(plan.session_id)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def is_valid(plan: Plan | None) -> bool:
    if plan is None:
        return False
    return plan.current_step < len(plan.steps)


def mark_done(session_id: str = "") -> Plan | None:
    plan = load_plan(session_id)
    if plan is None:
        return None
    if plan.current_step >= len(plan.steps):
        return plan
    plan.steps[plan.current_step].status = "done"
    plan.current_step += 1
    if plan.current_step < len(plan.steps):
        plan.steps[plan.current_step].status = "in_progress"
    save_plan(plan)
    return plan


def mark_blocked(reason: str, session_id: str = "") -> Plan | None:
    plan = load_plan(session_id)
    if plan is None:
        return None
    if plan.current_step >= len(plan.steps):
        return plan
    step = plan.steps[plan.current_step]
    step.status = "blocked"
    step.title = f"{step.title} [BLOCKED: {reason}]" if reason else f"{step.title} [BLOCKED]"
    save_plan(plan)
    return plan


def delete_plan(session_id: str = "") -> None:
    path = _plan_file(session_id)
    if path.exists():
        path.unlink()
