"""Tests for brain.state module."""

import json
import time

import pytest

from brain.state import (
    create_plan,
    delete_plan,
    is_valid,
    load_plan,
    mark_blocked,
    mark_done,
    save_plan,
)


@pytest.fixture
def mock_state_dir(tmp_path, monkeypatch):
    import brain.state as state_mod

    state_dir = tmp_path / "brain" / "state"
    plan_file = state_dir / "plan.json"
    monkeypatch.setattr(state_mod, "STATE_DIR", state_dir)
    monkeypatch.setattr(state_mod, "PLAN_FILE", plan_file)
    return state_dir


def _write_plan(
    prompt: str,
    step_titles: list[str],
    current_step: int,
    created_at: float | None = None,
    session_id: str = "",
    state_dir=None,
):
    import brain.state as state_mod

    sd = state_dir or state_mod.STATE_DIR
    sd.mkdir(parents=True, exist_ok=True)
    name = f"plan-{session_id}.json" if session_id else "plan.json"
    path = sd / name
    steps = [{"title": t, "status": "pending"} for t in step_titles]
    if current_step < len(steps):
        steps[current_step]["status"] = "in_progress"
    data = {
        "prompt": prompt,
        "steps": steps,
        "current_step": current_step,
        "created_at": created_at or time.time(),
        "session_id": session_id,
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestCreatePlan:
    def test_create_plan_sets_first_step_in_progress(self):
        plan = create_plan("do stuff", ["step 1", "step 2", "step 3"])
        assert plan.prompt == "do stuff"
        assert len(plan.steps) == 3
        assert plan.steps[0].status == "in_progress"
        assert plan.steps[1].status == "pending"
        assert plan.steps[2].status == "pending"
        assert plan.current_step == 0

    def test_single_step_plan(self):
        plan = create_plan("one", ["only step"])
        assert len(plan.steps) == 1
        assert plan.steps[0].status == "in_progress"
        assert plan.current_step == 0


class TestSaveAndLoad:
    def test_save_and_load_roundtrip(self, mock_state_dir):
        plan = create_plan("build thing", ["design", "implement", "test"])
        save_plan(plan)

        loaded = load_plan()
        assert loaded is not None
        assert loaded.prompt == "build thing"
        assert len(loaded.steps) == 3
        assert loaded.steps[0].title == "design"
        assert loaded.steps[0].status == "in_progress"
        assert loaded.current_step == 0

    def test_load_nonexistent_returns_none(self, mock_state_dir):
        assert load_plan() is None

    def test_load_corrupt_json_returns_none(self, mock_state_dir):
        import brain.state as state_mod

        state_mod.STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_mod.PLAN_FILE.write_text("not json at all {{{", encoding="utf-8")
        assert load_plan() is None

    def test_load_missing_keys_returns_none(self, mock_state_dir):
        import brain.state as state_mod

        state_mod.STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_mod.PLAN_FILE.write_text('{"prompt": "x"}', encoding="utf-8")
        assert load_plan() is None

    def test_atomic_save_does_not_corrupt(self, mock_state_dir):
        plan = create_plan("atomic", ["step1", "step2"])
        save_plan(plan)
        raw = mock_state_dir / "plan.json"
        content = raw.read_text(encoding="utf-8")
        data = json.loads(content)
        assert data["prompt"] == "atomic"
        assert len(data["steps"]) == 2


class TestMarkDone:
    def test_mark_done_advances_to_next_step(self, mock_state_dir):
        plan = create_plan("task", ["step A", "step B", "step C"])
        save_plan(plan)

        updated = mark_done()
        assert updated is not None
        assert updated.steps[0].status == "done"
        assert updated.steps[1].status == "in_progress"
        assert updated.steps[2].status == "pending"
        assert updated.current_step == 1

    def test_mark_done_on_last_step_completes(self, mock_state_dir):
        plan = create_plan("done", ["final step"])
        save_plan(plan)

        updated = mark_done()
        assert updated is not None
        assert updated.steps[0].status == "done"
        assert updated.current_step == 1
        assert updated.current_step >= len(updated.steps)

    def test_mark_done_on_complete_plan_noops(self, mock_state_dir):
        plan = create_plan("done already", ["only"])
        save_plan(plan)
        mark_done()  # complete
        updated = mark_done()  # noop
        assert updated is not None
        assert updated.current_step == 1

    def test_mark_done_nonexistent_returns_none(self, mock_state_dir):
        assert mark_done() is None


class TestMarkBlocked:
    def test_mark_blocked_does_not_advance(self, mock_state_dir):
        plan = create_plan("stuck", ["step 1", "step 2"])
        save_plan(plan)

        updated = mark_blocked("reason")
        assert updated is not None
        assert updated.steps[0].status == "blocked"
        assert "BLOCKED" in updated.steps[0].title
        assert updated.current_step == 0  # did not advance


class TestIsValid:
    def test_valid_when_remaining_steps(self, mock_state_dir):
        plan = create_plan("valid", ["step"])
        save_plan(plan)
        assert is_valid(load_plan()) is True

    def test_invalid_when_all_steps_done(self, mock_state_dir):
        import brain.state as state_mod

        state_mod.STATE_DIR.mkdir(parents=True, exist_ok=True)
        state_mod.PLAN_FILE.write_text(
            json.dumps(
                {
                    "prompt": "done plan",
                    "steps": [{"title": "only", "status": "done"}],
                    "current_step": 1,
                    "created_at": time.time(),
                }
            ),
            encoding="utf-8",
        )
        assert is_valid(load_plan()) is False


class TestDeletePlan:
    def test_delete_removes_file(self, mock_state_dir):
        plan = create_plan("del", ["s1"])
        save_plan(plan)
        assert load_plan() is not None
        delete_plan()
        assert load_plan() is None

    def test_delete_nonexistent_does_not_crash(self, mock_state_dir):
        delete_plan()  # should not raise


class TestSessionIsolation:
    def test_save_with_session_id_creates_isolated_file(self, mock_state_dir):
        plan_a = create_plan("task a", ["step a1"], session_id="thread-a")
        save_plan(plan_a)
        assert (mock_state_dir / "plan-thread-a.json").exists()
        assert not (mock_state_dir / "plan.json").exists()

    def test_load_session_isolation(self, mock_state_dir):
        _write_plan("task a", ["step a1"], 0, session_id="thread-a", state_dir=mock_state_dir)
        _write_plan("task b", ["step b1"], 0, session_id="thread-b", state_dir=mock_state_dir)

        plan_a = load_plan("thread-a")
        plan_b = load_plan("thread-b")
        assert plan_a is not None and plan_a.prompt == "task a"
        assert plan_b is not None and plan_b.prompt == "task b"

    def test_load_default_backward_compat(self, mock_state_dir):
        _write_plan("default", ["step"], 0, state_dir=mock_state_dir)
        loaded = load_plan()
        assert loaded is not None and loaded.prompt == "default"

    def test_mark_done_with_session_id(self, mock_state_dir):
        _write_plan("multi", ["step 1", "step 2"], 0, session_id="s1", state_dir=mock_state_dir)
        updated = mark_done("s1")
        assert updated is not None
        assert updated.current_step == 1
        assert updated.steps[0].status == "done"
        assert updated.steps[1].status == "in_progress"

    def test_mark_blocked_with_session_id(self, mock_state_dir):
        _write_plan("stuck", ["step 1"], 0, session_id="s1", state_dir=mock_state_dir)
        updated = mark_blocked("reason", "s1")
        assert updated is not None
        assert updated.steps[0].status == "blocked"

    def test_delete_plan_with_session_id(self, mock_state_dir):
        _write_plan("del", ["step"], 0, session_id="s1", state_dir=mock_state_dir)
        assert (mock_state_dir / "plan-s1.json").exists()
        delete_plan("s1")
        assert not (mock_state_dir / "plan-s1.json").exists()

    def test_is_valid_no_expires_at(self, mock_state_dir):
        _write_plan("valid", ["step 1", "step 2"], 0, state_dir=mock_state_dir)
        assert is_valid(load_plan()) is True

        import brain.state as state_mod

        state_mod.PLAN_FILE.write_text(
            json.dumps(
                {
                    "prompt": "done",
                    "steps": [{"title": "only", "status": "done"}],
                    "current_step": 1,
                    "created_at": time.time(),
                }
            ),
            encoding="utf-8",
        )
        assert is_valid(load_plan()) is False
