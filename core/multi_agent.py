"""Safe multi-agent coordination primitives for YasinCoder.

The coordinator keeps agents isolated by role, permission policy, budget and
workspace locks. It is deliberately provider-neutral: callers supply the
actual agent function, so credentials never need to be copied into shared
state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event, RLock
from typing import Callable, Mapping

from core.permissions import PermissionPolicy


class AgentError(RuntimeError):
    """Base error for multi-agent execution."""


class AgentCancelled(AgentError):
    """Raised when a task is cancelled before or during execution."""


class AgentBudgetExceeded(AgentError):
    """Raised when an agent exceeds its configured execution budget."""


class WorkspaceConflict(AgentError):
    """Raised when two agents request overlapping write ownership."""


@dataclass(frozen=True)
class AgentRole:
    name: str
    capabilities: tuple[str, ...] = ("read",)
    max_steps: int = 20
    max_output_chars: int = 20000

    def allows(self, capability: str) -> bool:
        return capability in self.capabilities


@dataclass
class AgentTask:
    task_id: str
    role: AgentRole
    prompt: str
    files: tuple[str, ...] = ()
    permissions: PermissionPolicy = field(default_factory=PermissionPolicy)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    task_id: str
    agent: str
    output: str
    steps: int
    files: tuple[str, ...] = ()


class WorkspaceLock:
    """In-process path ownership registry with overlap prevention."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._owners: dict[str, str] = {}

    @staticmethod
    def _overlap(a: str, b: str) -> bool:
        a = a.rstrip("/") or "/"
        b = b.rstrip("/") or "/"
        return a == b or a.startswith(b + "/") or b.startswith(a + "/")

    def acquire(self, owner: str, paths: tuple[str, ...]) -> None:
        with self._lock:
            for path in paths:
                for existing, existing_owner in self._owners.items():
                    if existing_owner != owner and self._overlap(path, existing):
                        raise WorkspaceConflict(f"workspace path is owned by {existing_owner}: {path}")
            for path in paths:
                self._owners[path.rstrip("/") or "/"] = owner

    def release(self, owner: str) -> None:
        with self._lock:
            self._owners = {path: who for path, who in self._owners.items() if who != owner}

    def snapshot(self) -> dict[str, str]:
        with self._lock:
            return dict(self._owners)


class SharedTaskContext:
    """Small, JSON-like coordination state; secrets should never be stored here."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._values: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        if any(token in key.lower() for token in ("key", "token", "secret", "password", "credential")):
            raise ValueError("credential-like context keys are not permitted")
        with self._lock:
            self._values[key] = value

    def get(self, key: str, default: object = None) -> object:
        with self._lock:
            return self._values.get(key, default)

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return dict(self._values)


class MultiAgentCoordinator:
    """Run specialized agents under shared safety controls."""

    def __init__(self, *, context: SharedTaskContext | None = None, workspace: WorkspaceLock | None = None) -> None:
        self.context = context or SharedTaskContext()
        self.workspace = workspace or WorkspaceLock()
        self._cancelled: set[str] = set()
        self._cancel_lock = RLock()

    def cancel(self, task_id: str) -> None:
        with self._cancel_lock:
            self._cancelled.add(task_id)

    def is_cancelled(self, task_id: str) -> bool:
        with self._cancel_lock:
            return task_id in self._cancelled

    def _validate(self, task: AgentTask) -> None:
        if task.role.max_steps < 1 or task.role.max_output_chars < 1:
            raise AgentBudgetExceeded("invalid agent budget")
        for capability in task.role.capabilities:
            if not task.permissions.allows(capability):
                raise AgentError(f"role capability is not granted by policy: {capability}")
        if "write" in task.role.capabilities and not task.permissions.allows("write"):
            raise AgentError("write capability requires explicit permission")

    def run(
        self,
        task: AgentTask,
        worker: Callable[[AgentTask, Callable[[], None]], str],
    ) -> AgentResult:
        self._validate(task)
        if self.is_cancelled(task.task_id):
            raise AgentCancelled(task.task_id)
        self.workspace.acquire(task.task_id, task.files if "write" in task.role.capabilities else ())
        steps = 0

        def checkpoint() -> None:
            nonlocal steps
            steps += 1
            if self.is_cancelled(task.task_id):
                raise AgentCancelled(task.task_id)
            if steps > task.role.max_steps:
                raise AgentBudgetExceeded(task.task_id)

        try:
            output = str(worker(task, checkpoint))
            if len(output) > task.role.max_output_chars:
                raise AgentBudgetExceeded("agent output budget exceeded")
            return AgentResult(task.task_id, task.role.name, output, steps, task.files)
        finally:
            self.workspace.release(task.task_id)


DEFAULT_ROLES: Mapping[str, AgentRole] = {
    "planner": AgentRole("planner", ("read",), 30),
    "researcher": AgentRole("researcher", ("read", "network"), 40),
    "coder": AgentRole("coder", ("read", "write"), 50),
    "reviewer": AgentRole("reviewer", ("read",), 30),
    "tester": AgentRole("tester", ("read", "execute"), 40),
}
