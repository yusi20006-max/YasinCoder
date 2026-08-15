"""Bounded autonomous coding orchestration.

The engine separates planning, execution, verification, permissions, and
checkpoint persistence. It never executes a model-generated tool directly:
tool calls go through the existing agent_tools permission/sandbox layer.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from core.agent_tools import execute as execute_tool
from core.runtime import user_data_dir
from core.test_generator import TestGenerator
from providers.manager import ProviderManager


ALLOWED_TOOLS = {"workspace.info", "file.read", "file.write", "search", "shell.exec", "git.exec", "test.run"}
RISKY_TOOLS = {"file.write", "shell.exec", "git.exec"}
TERMINAL_STATUSES = {"completed", "failed", "blocked", "stopped"}


class AutonomousError(RuntimeError):
    pass


class PlanValidationError(AutonomousError):
    pass


@dataclass
class PlanStep:
    id: str
    description: str
    tool: str
    payload: dict[str, Any] = field(default_factory=dict)
    verify: str = ""
    risk: str = "safe"
    status: str = "pending"
    result: dict[str, Any] | None = None


@dataclass
class ExecutionPlan:
    task: str
    steps: list[PlanStep]
    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = "planned"
    current_step: int = 0
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CheckpointStore:
    """Small atomic JSON store used for resumable autonomous runs."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or user_data_dir()) / "autonomous"
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, plan_id: str) -> Path:
        return self.root / f"{plan_id}.json"

    def save(self, plan: ExecutionPlan) -> Path:
        target = self.path(plan.plan_id)
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(plan.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        temp.replace(target)
        return target

    def load(self, plan_id: str) -> ExecutionPlan:
        data = json.loads(self.path(plan_id).read_text(encoding="utf-8"))
        return plan_from_dict(data)


def plan_from_dict(data: dict[str, Any]) -> ExecutionPlan:
    steps = [PlanStep(**step) for step in data.get("steps", [])]
    return ExecutionPlan(
        task=str(data.get("task", "")),
        steps=steps,
        plan_id=str(data.get("plan_id") or uuid.uuid4().hex),
        status=str(data.get("status", "planned")),
        current_step=int(data.get("current_step", 0)),
        error=data.get("error"),
    )


def _json_object(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        value = value.strip("`")
        if value.startswith("json"):
            value = value[4:].lstrip()
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PlanValidationError("planner returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise PlanValidationError("planner response must be a JSON object")
    return data


def validate_plan(data: dict[str, Any], *, max_steps: int = 12) -> ExecutionPlan:
    task = str(data.get("task", "")).strip()
    raw_steps = data.get("steps")
    if not task or not isinstance(raw_steps, list) or not raw_steps:
        raise PlanValidationError("plan requires a task and at least one step")
    if len(raw_steps) > max_steps:
        raise PlanValidationError(f"plan exceeds maximum of {max_steps} steps")

    steps: list[PlanStep] = []
    for index, raw in enumerate(raw_steps, 1):
        if not isinstance(raw, dict):
            raise PlanValidationError(f"step {index} is invalid")
        tool = str(raw.get("tool", "")).strip()
        if tool not in ALLOWED_TOOLS:
            raise PlanValidationError(f"step {index} uses unsupported tool: {tool or 'empty'}")
        payload = raw.get("payload") or {}
        if not isinstance(payload, dict):
            raise PlanValidationError(f"step {index} payload must be an object")
        risk = str(raw.get("risk", "safe")).lower().strip()
        if tool in RISKY_TOOLS:
            risk = "risky"
        steps.append(PlanStep(
            id=str(raw.get("id") or f"step-{index}"),
            description=str(raw.get("description") or f"Run {tool}"),
            tool=tool,
            payload=payload,
            verify=str(raw.get("verify") or ""),
            risk=risk,
        ))
    return ExecutionPlan(task=task, steps=steps)


class ModelPlanner:
    """Use the configured provider only for structured planning."""

    def __init__(self, provider: ProviderManager | None = None):
        self.provider = provider or ProviderManager()

    def create(self, task: str, *, max_steps: int = 12) -> ExecutionPlan:
        prompt = f"""Create a bounded execution plan for this coding task.\n\nTASK:\n{task}\n\nReturn JSON only with this shape:\n{{\n  \"task\": "...",\n  \"steps\": [{{\"id\": \"step-1\", \"description\": "...", \"tool\": "file.read|file.write|search|workspace.info|shell.exec|git.exec|test.run", \"payload\": {{}}, \"verify\": "...", \"risk\": \"safe|risky\"}}]\n}}\n\nMaximum {max_steps} bounded steps. Prefer read/search before writes. Never invent credentials. Keep payloads limited to the current workspace."""
        return validate_plan(_json_object(self.provider.ask(prompt)), max_steps=max_steps)


class AutonomousEngine:
    """Plan, execute, verify and checkpoint one bounded coding run."""

    def __init__(
        self,
        *,
        planner: ModelPlanner | Callable[[str], ExecutionPlan] | None = None,
        tool_runner: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
        verifier: Callable[[PlanStep, dict[str, Any]], bool] | None = None,
        approval: Callable[[PlanStep], bool] | None = None,
        checkpoints: CheckpointStore | None = None,
        max_steps: int = 12,
        verify_generated_tests: bool = False,
        workspace: str | Path | None = None,
    ):
        self.planner = planner or ModelPlanner()
        self.tool_runner = tool_runner or self._run_tool
        self.verifier = verifier or self._default_verify
        self.approval = approval
        self.checkpoints = checkpoints or CheckpointStore()
        self.max_steps = max_steps
        self.verify_generated_tests = verify_generated_tests
        self.workspace = Path(workspace or Path.cwd()).expanduser().resolve()

    @staticmethod
    def _run_tool(tool: str, payload: dict[str, Any]) -> dict[str, Any]:
        return execute_tool(tool, payload)

    @staticmethod
    def _default_verify(step: PlanStep, result: dict[str, Any]) -> bool:
        return bool(result.get("ok"))

    def _verify_generated_tests(self) -> dict[str, Any]:
        generator = TestGenerator(self.workspace)
        report = generator.generate(changed_only=True)
        if not report.supported:
            return {"ok": False, "error": "test generator does not support this project", "generation": report.as_dict()}
        result = generator.run()
        result["generation"] = report.as_dict()
        return result

    def plan(self, task: str) -> ExecutionPlan:
        if not task.strip():
            raise PlanValidationError("task must not be empty")
        if isinstance(self.planner, ModelPlanner):
            plan = self.planner.create(task, max_steps=self.max_steps)
        else:
            plan = self.planner(task)
        if not isinstance(plan, ExecutionPlan):
            raise PlanValidationError("planner must return ExecutionPlan")
        if len(plan.steps) > self.max_steps:
            raise PlanValidationError(f"plan exceeds maximum of {self.max_steps} steps")
        self.checkpoints.save(plan)
        return plan

    def run(self, plan: ExecutionPlan, *, resume: bool = True) -> ExecutionPlan:
        if resume and self.checkpoints.path(plan.plan_id).exists():
            plan = self.checkpoints.load(plan.plan_id)
        plan.status = "running"
        self.checkpoints.save(plan)

        while plan.current_step < len(plan.steps):
            step = plan.steps[plan.current_step]
            if step.status in TERMINAL_STATUSES:
                plan.current_step += 1
                continue
            if step.tool in RISKY_TOOLS and self.approval is not None and not self.approval(step):
                step.status = "blocked"
                plan.status = "blocked"
                plan.error = f"approval required for {step.tool}"
                self.checkpoints.save(plan)
                return plan
            if step.tool in RISKY_TOOLS and self.approval is None:
                step.status = "blocked"
                plan.status = "blocked"
                plan.error = f"approval required for {step.tool}"
                self.checkpoints.save(plan)
                return plan

            try:
                result = self.tool_runner(step.tool, dict(step.payload))
            except Exception as exc:
                step.status = "failed"
                step.result = {"ok": False, "error": str(exc)}
                plan.status = "failed"
                plan.error = f"step {step.id} failed"
                self.checkpoints.save(plan)
                return plan

            step.result = result
            if not result.get("ok"):
                step.status = "failed"
                plan.status = "failed"
                plan.error = f"step {step.id} failed"
                self.checkpoints.save(plan)
                return plan
            if not self.verifier(step, result):
                step.status = "failed"
                plan.status = "failed"
                plan.error = f"verification failed for {step.id}"
                self.checkpoints.save(plan)
                return plan

            step.status = "completed"
            plan.current_step += 1
            self.checkpoints.save(plan)

        if self.verify_generated_tests:
            generated_result = self._verify_generated_tests()
            plan.error = None
            plan.status = "completed" if generated_result.get("ok") else "failed"
            if not generated_result.get("ok"):
                plan.error = "generated-test verification failed"
            plan.steps.append(PlanStep(
                id="generated-tests",
                description="Generate and execute focused verification tests",
                tool="test.run",
                payload={"generated": True},
                verify="generated tests pass",
                status="completed" if generated_result.get("ok") else "failed",
                result=generated_result,
            ))
            self.checkpoints.save(plan)
            return plan

        plan.status = "completed"
        self.checkpoints.save(plan)
        return plan

    def run_task(self, task: str) -> ExecutionPlan:
        return self.run(self.plan(task))

    def resume(self, plan_id: str) -> ExecutionPlan:
        plan = self.checkpoints.load(plan_id)
        if plan.status == "completed":
            return plan
        return self.run(plan, resume=False)
