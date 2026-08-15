import json
import tempfile
import unittest
from pathlib import Path

from core.autonomous import (
    AutonomousEngine,
    CheckpointStore,
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


class AutonomousEngineTests(unittest.TestCase):
    def test_plan_rejects_unknown_tools(self):
        with self.assertRaises(PlanValidationError):
            validate_plan({"task": "x", "steps": [{"tool": "rm -rf"}]})

    def test_plan_is_bounded(self):
        steps = [{"tool": "workspace.info"} for _ in range(3)]
        with self.assertRaises(PlanValidationError):
            validate_plan({"task": "x", "steps": steps}, max_steps=2)

    def test_engine_executes_and_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            store = CheckpointStore(Path(tmp))

            def runner(tool, payload):
                calls.append((tool, payload))
                return {"ok": True, "tool": tool}

            engine = AutonomousEngine(
                planner=lambda _task: make_plan(),
                tool_runner=runner,
                checkpoints=store,
            )
            plan = engine.run_task("inspect")

            self.assertEqual(plan.status, "completed")
            self.assertEqual(plan.steps[0].status, "completed")
            self.assertEqual(calls, [("workspace.info", {})])
            saved = json.loads(store.path(plan.plan_id).read_text())
            self.assertEqual(saved["status"], "completed")

    def test_risky_step_requires_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(Path(tmp))
            plan = make_plan("file.write")
            engine = AutonomousEngine(
                planner=lambda _task: plan,
                tool_runner=lambda *_: {"ok": True},
                checkpoints=store,
            )
            result = engine.run_task("write")
            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.steps[0].status, "blocked")

    def test_risky_step_can_run_after_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(Path(tmp))
            plan = make_plan("file.write")
            calls = []
            engine = AutonomousEngine(
                planner=lambda _task: plan,
                tool_runner=lambda tool, payload: calls.append((tool, payload)) or {"ok": True},
                approval=lambda _step: True,
                checkpoints=store,
            )
            result = engine.run_task("write")
            self.assertEqual(result.status, "completed")
            self.assertEqual(calls[0][0], "file.write")

    def test_resume_skips_completed_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CheckpointStore(Path(tmp))
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
            self.assertEqual(result.status, "completed")
            self.assertEqual(calls, [])

    def test_generated_test_verification_is_optional_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sample.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
            store = CheckpointStore(root / "state")
            engine = AutonomousEngine(
                planner=lambda _task: make_plan(),
                tool_runner=lambda *_: {"ok": True},
                checkpoints=store,
                verify_generated_tests=True,
                workspace=root,
            )
            result = engine.run_task("verify")
            self.assertEqual(result.status, "completed")
            self.assertEqual(result.steps[-1].id, "generated-tests")
            self.assertEqual(result.steps[-1].result["ok"], True)
