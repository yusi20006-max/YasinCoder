import json
from pathlib import Path

from core.autonomous import (
    AutonomousEngine,
    CheckpointStore,
    ExecutionPlan,
    PlanValidationError,
    validate_plan,
)


def make_plan(tool="workspace.info"):
    return validate_plan({
        "task": "inspect workspace",
        "steps": [{
            "id": "step-1",
            "description": "inspect",
            "tool": tool,
            "payload": {},
            "verify": "ok",
        }],
    })


def test_plan_rejects_unknown_tools():
    try:
        validate_plan({"task": "x", "steps": [{"tool": "rm -rf"}]})
    except PlanValidationError:
        return
    assert False, "unknown tool must be rejected"


def test_plan_is_bounded():
    steps = [{"tool": "workspace.info"} for _ in range(3)]
    try:
        validate_plan({"task": "x", "steps": steps}, max_steps=2)
    except PlanValidationError:
        return
    assert False, "oversized plan must be rejected"


def test_engine_executes_and_checkpoints(tmp_path):
    calls = []
    store = CheckpointStore(tmp_path)

    def planner(_task):
        return make_plan()

    def runner(tool, payload):
        calls.append((tool, payload))
        return {"ok": True, "tool": tool}

    engine = AutonomousEngine(planner=planner, tool_runner=runner, checkpoints=store)
    plan = engine.run_task("inspect")

    assert plan.status == "completed"
    assert plan.steps[0].status == "completed"
    assert calls == [("workspace.info", {})]
    saved = json.loads(store.path(plan.plan_id).read_text())
    assert saved["status"] == "completed"


def test_risky_step_requires_approval(tmp_path):
    store = CheckpointStore(tmp_path)
    plan = make_plan("file.write")
    engine = AutonomousEngine(
        planner=lambda _task: plan,
        tool_runner=lambda *_: {"ok": True},
        checkpoints=store,
    )
    result = engine.run_task("write")
    assert result.status == "blocked"
    assert result.steps[0].status == "blocked"


def test_risky_step_can_run_after_approval(tmp_path):
    store = CheckpointStore(tmp_path)
    plan = make_plan("file.write")
    calls = []
    engine = AutonomousEngine(
        planner=lambda _task: plan,
        tool_runner=lambda tool, payload: calls.append((tool, payload)) or {"ok": True},
        approval=lambda _step: True,
        checkpoints=store,
    )
    result = engine.run_task("write")
    assert result.status == "completed"
    assert calls[0][0] == "file.write"


def test_resume_skips_completed_steps(tmp_path):
    store = CheckpointStore(tmp_path)
    plan = make_plan()
    plan.steps[0].status = "completed"
    plan.current_step = 1
    plan.status = "running"
    store.save(plan)
    calls = []
    engine = AutonomousEngine(
        planner=lambda _task: plan,
        tool_runner=lambda tool, payload: calls.append(tool) or {"ok": True},
        checkpoints=store,
    )
    result = engine.resume(plan.plan_id)
    assert result.status == "completed"
    assert calls == []
