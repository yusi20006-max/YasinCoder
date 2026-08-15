import json

from core.autonomous import AutonomousEngine, PlanValidationError


class AutonomousCommand:
    """Plan and execute a bounded autonomous coding task.

    Mutating tools remain blocked unless the caller explicitly grants approval
    through the engine API; the CLI therefore defaults to a safe plan-only mode.
    """

    def plan(self, task: str) -> str:
        engine = AutonomousEngine()
        return json.dumps(engine.plan(task).as_dict(), indent=2, ensure_ascii=False)

    def run(self, task: str) -> str:
        try:
            engine = AutonomousEngine()
            plan = engine.run_task(task)
            return json.dumps(plan.as_dict(), indent=2, ensure_ascii=False)
        except PlanValidationError as exc:
            return json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False)
