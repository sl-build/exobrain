"""ExoBrain CLI plugin — think + plan + gate for Hermes Agent."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from . import schemas

logger = logging.getLogger(__name__)

_PLAN_PATH_TEMPLATE = Path.home() / ".exobrain" / "state"
_GATED_TOOLS = {"terminal", "write_file", "patch", "file_edit", "edit", "bash", "task"}


def _plan_file(session_id: str = "") -> Path:
    if session_id:
        return _PLAN_PATH_TEMPLATE / f"plan-{session_id}.json"
    return _PLAN_PATH_TEMPLATE / "plan.json"


def _run_brain(*args: str) -> str:
    try:
        result = subprocess.run(
            ["exobrain", *args],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip() or "unknown error"
            return json.dumps({"error": f"exobrain failed (exit {result.returncode}): {err}"})
        return json.dumps({"result": output})
    except FileNotFoundError:
        return json.dumps({"error": "exobrain CLI not installed. Run: uv tool install exobrain"})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "exobrain CLI timed out"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _read_plan(session_id: str = "") -> Optional[Dict[str, Any]]:
    plan_path = _plan_file(session_id)
    if not plan_path.exists():
        return None
    try:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    steps = data.get("steps", [])
    current = data.get("current_step", 0)
    if current >= len(steps):
        return None
    return data


def _handle_brain_think(args: dict, **kwargs) -> str:
    prompt = args.get("prompt", "").strip()
    if not prompt:
        return json.dumps({"error": "No prompt provided"})
    cmd = ["think", "--plan", prompt]
    session_id = kwargs.get("session_id", "")
    if session_id:
        cmd.extend(["--session-id", session_id])
    return _run_brain(*cmd)


def _handle_plan_done(args: dict, **kwargs) -> str:
    cmd = ["plan", "done"]
    session_id = kwargs.get("session_id", "")
    if session_id:
        cmd.extend(["--session-id", session_id])
    return _run_brain(*cmd)


def _handle_plan_block(args: dict, **kwargs) -> str:
    reason = args.get("reason", "").strip()
    cmd = ["plan", "block"]
    if reason:
        cmd.append(reason)
    session_id = kwargs.get("session_id", "")
    if session_id:
        cmd.extend(["--session-id", session_id])
    return _run_brain(*cmd)


def _handle_plan_status(args: dict, **kwargs) -> str:
    session_id = kwargs.get("session_id", "")
    cmd = ["plan"]
    if session_id:
        cmd.extend(["--session-id", session_id])
    return _run_brain(*cmd)


def _on_pre_tool_call(
    tool_name: str, args: dict, task_id: str, **kwargs
) -> Optional[Dict[str, Any]]:
    if tool_name not in _GATED_TOOLS:
        return None
    session_id = kwargs.get("session_id", "")
    plan = _read_plan(session_id)
    if plan is not None:
        return None
    return {"action": "block", "message": "⛔ No active plan. Call brain_think to create one."}


def _on_post_receive_message(content: str = "", session_id: str = "", **kwargs) -> str:
    plan = _read_plan(session_id)
    if plan is None:
        return ""
    steps = plan.get("steps", [])
    current = plan.get("current_step", 0)
    total = len(steps)
    if current >= total:
        return ""
    current_title = steps[current].get("title", "") if current < total else ""
    msg = f"🧠 {current + 1}/{total} → {current_title}"
    return msg[:120]


def register(ctx):
    ctx.register_tool(
        name="brain_think",
        toolset="brain",
        schema=schemas.BRAIN_THINK,
        handler=_handle_brain_think,
    )
    ctx.register_tool(
        name="brain_plan_done",
        toolset="brain",
        schema=schemas.BRAIN_PLAN_DONE,
        handler=_handle_plan_done,
    )
    ctx.register_tool(
        name="brain_plan_block",
        toolset="brain",
        schema=schemas.BRAIN_PLAN_BLOCK,
        handler=_handle_plan_block,
    )
    ctx.register_tool(
        name="brain_plan_status",
        toolset="brain",
        schema=schemas.BRAIN_PLAN_STATUS,
        handler=_handle_plan_status,
    )
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
    ctx.register_hook("post_receive_message", _on_post_receive_message)
