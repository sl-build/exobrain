"""Tests for brain-tool Hermes plugin."""

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugin" / "brain-tool"


def _import_plugin():
    """Load brain_tool plugin via importlib (dir name has hyphen)."""
    import importlib.util

    mod_name = "brain_tool_test"
    schemas_name = f"{mod_name}.schemas"

    schemas_spec = importlib.util.spec_from_file_location(schemas_name, PLUGIN_DIR / "schemas.py")
    schemas = importlib.util.module_from_spec(schemas_spec)
    sys.modules[schemas_name] = schemas
    schemas_spec.loader.exec_module(schemas)

    init_spec = importlib.util.spec_from_file_location(mod_name, PLUGIN_DIR / "__init__.py")
    bt = importlib.util.module_from_spec(init_spec)
    sys.modules[mod_name] = bt
    init_spec.loader.exec_module(bt)

    return bt


@pytest.fixture(scope="session")
def plugin():
    return _import_plugin()


@pytest.fixture
def mock_plan_dir(plugin, tmp_path, monkeypatch):
    monkeypatch.setattr(plugin, "_PLAN_PATH_TEMPLATE", tmp_path)
    return tmp_path


def _make_plan(path: Path, steps: list[str], current_step: int = 0):
    data = {
        "prompt": "test",
        "steps": [
            {"title": t, "status": "in_progress" if i == current_step else "pending"}
            for i, t in enumerate(steps)
        ],
        "current_step": current_step,
        "created_at": time.time(),
        "session_id": "",
    }
    path.write_text(json.dumps(data), encoding="utf-8")


# ── _read_plan ──────────────────────────────────────────────────────


class TestReadPlan:
    def test_exists_valid(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", ["step 1", "step 2"])
        result = plugin._read_plan()
        assert result is not None
        assert result["current_step"] == 0
        assert len(result["steps"]) == 2

    def test_nonexistent(self, plugin, mock_plan_dir):
        assert plugin._read_plan() is None

    def test_corrupt_json(self, plugin, mock_plan_dir):
        (mock_plan_dir / "plan.json").write_text("{{{ not json", encoding="utf-8")
        assert plugin._read_plan() is None

    def test_all_steps_done(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", ["only"], current_step=1)
        assert plugin._read_plan() is None

    def test_session_isolation(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan-a.json", ["step a1"])
        assert plugin._read_plan("a") is not None
        assert plugin._read_plan("b") is None

    def test_session_file_with_hyphen_in_id(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan-thread-42.json", ["step"])
        assert plugin._read_plan("thread-42") is not None

    def test_oserror_returns_none(self, plugin, mock_plan_dir):
        p = mock_plan_dir / "plan.json"
        p.mkdir(parents=True)
        assert plugin._read_plan() is None

    def test_empty_steps_list_returns_none(self, plugin, mock_plan_dir):
        p = mock_plan_dir / "plan.json"
        p.write_text(
            json.dumps(
                {
                    "prompt": "empty",
                    "steps": [],
                    "current_step": 0,
                    "created_at": time.time(),
                }
            ),
            encoding="utf-8",
        )
        assert plugin._read_plan() is None


# ── _on_post_receive_message ────────────────────────────────────────


class TestPostReceiveMessage:
    def test_active_plan(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", ["Analyse logs", "Fix parser", "Deploy"])
        msg = plugin._on_post_receive_message()
        assert msg == "🧠 1/3 → Analyse logs"

    def test_mid_plan(self, plugin, mock_plan_dir):
        _make_plan(
            mock_plan_dir / "plan.json", ["Analyse logs", "Fix parser", "Deploy"], current_step=1
        )
        msg = plugin._on_post_receive_message()
        assert msg == "🧠 2/3 → Fix parser"

    def test_no_plan(self, plugin, mock_plan_dir):
        assert plugin._on_post_receive_message() == ""

    def test_plan_completed(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", ["only"], current_step=1)
        assert plugin._on_post_receive_message() == ""

    def test_truncates_long_title(self, plugin, mock_plan_dir):
        long_title = "Implement the authentication module with OAuth2 and JWT tokens for user session management and role-based access control across the entire platform"
        _make_plan(mock_plan_dir / "plan.json", [long_title])
        msg = plugin._on_post_receive_message()
        assert len(msg) <= 120
        assert msg.startswith("🧠 1/1 → ")

    def test_passes_session_id(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan-s1.json", ["Step 1"])
        msg = plugin._on_post_receive_message(session_id="s1")
        assert msg == "🧠 1/1 → Step 1"
        assert plugin._on_post_receive_message(session_id="s2") == ""

    def test_empty_title_step(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", [""])
        msg = plugin._on_post_receive_message()
        assert msg == "🧠 1/1 → "


# ── _on_pre_tool_call ───────────────────────────────────────────────


class TestPreToolCall:
    def test_blocks_gated_without_plan(self, plugin, mock_plan_dir):
        result = plugin._on_pre_tool_call("terminal", {"cmd": "ls"}, "t1")
        assert result is not None
        assert result["action"] == "block"

    def test_allows_gated_with_plan(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", ["step"])
        result = plugin._on_pre_tool_call("terminal", {"cmd": "ls"}, "t1")
        assert result is None

    def test_allows_nongated_tool(self, plugin, mock_plan_dir):
        result = plugin._on_pre_tool_call("read_file", {"path": "x"}, "t1")
        assert result is None

    def test_blocks_all_gated_tools(self, plugin, mock_plan_dir):
        for tool in plugin._GATED_TOOLS:
            result = plugin._on_pre_tool_call(tool, {}, "t1")
            assert result is not None, f"{tool} was not blocked"
            assert result["action"] == "block"

    def test_session_id_isolation(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan-a.json", ["step"])
        blocked = plugin._on_pre_tool_call("bash", {}, "t1", session_id="b")
        allowed = plugin._on_pre_tool_call("bash", {}, "t1", session_id="a")
        assert blocked is not None
        assert allowed is None

    def test_plan_completed_allows_gate(self, plugin, mock_plan_dir):
        _make_plan(mock_plan_dir / "plan.json", ["step"], current_step=1)
        result = plugin._on_pre_tool_call("terminal", {}, "t1")
        assert result is not None
        assert result["action"] == "block"


# ── Handler helpers ─────────────────────────────────────────────────


class TestHandlers:
    def test_think_passes_session_id(self, plugin, mock_plan_dir):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_brain_think({"prompt": "test"}, session_id="s1")
            args = mock_run.call_args[0]
            assert "--session-id" in args
            idx = args.index("--session-id")
            assert args[idx + 1] == "s1"

    def test_think_no_session_id(self, plugin, mock_plan_dir):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_brain_think({"prompt": "test"})
            args = mock_run.call_args[0]
            assert "--session-id" not in args

    def test_think_empty_prompt_returns_error(self, plugin):
        result = plugin._handle_brain_think({"prompt": "  "})
        data = json.loads(result)
        assert "error" in data

    def test_plan_done_passes_session_id(self, plugin, mock_plan_dir):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_plan_done({}, session_id="s1")
            args = mock_run.call_args[0]
            assert "--session-id" in args
            idx = args.index("--session-id")
            assert args[idx + 1] == "s1"

    def test_plan_done_no_session_id(self, plugin):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_plan_done({})
            args = mock_run.call_args[0]
            assert "--session-id" not in args

    def test_plan_block_passes_session_id(self, plugin):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_plan_block({"reason": "stuck"}, session_id="s1")
            args = mock_run.call_args[0]
            assert "--session-id" in args
            idx = args.index("--session-id")
            assert args[idx + 1] == "s1"

    def test_plan_block_passes_reason(self, plugin):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_plan_block({"reason": "stuck"})
            args = mock_run.call_args[0]
            assert "stuck" in args
            assert "block" in args

    def test_plan_status_passes_session_id(self, plugin):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_plan_status({}, session_id="s1")
            args = mock_run.call_args[0]
            assert "--session-id" in args
            idx = args.index("--session-id")
            assert args[idx + 1] == "s1"

    def test_plan_status_no_session_id(self, plugin):
        with patch.object(plugin, "_run_brain") as mock_run:
            mock_run.return_value = json.dumps({"result": "ok"})
            plugin._handle_plan_status({})
            args = mock_run.call_args[0]
            assert args == ("plan",)
