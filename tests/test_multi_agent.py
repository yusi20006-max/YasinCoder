import unittest

from core.multi_agent import (
    AgentBudgetExceeded,
    AgentRole,
    AgentTask,
    MultiAgentCoordinator,
    SharedTaskContext,
    WorkspaceConflict,
)
from core.permissions import PermissionPolicy


class MultiAgentTests(unittest.TestCase):
    def setUp(self):
        self.coordinator = MultiAgentCoordinator()

    def test_specialized_agent_runs_with_budget(self):
        role = AgentRole("coder", ("read", "write"), max_steps=2)
        task = AgentTask(
            "t1", role, "implement", ("src/a.py",),
            PermissionPolicy(read=True, write=True),
        )

        def worker(_task, checkpoint):
            checkpoint()
            return "done"

        result = self.coordinator.run(task, worker)
        self.assertEqual(result.agent, "coder")
        self.assertEqual(result.output, "done")
        self.assertEqual(self.coordinator.workspace.snapshot(), {})

    def test_overlapping_writes_are_rejected(self):
        role = AgentRole("coder", ("read", "write"))
        policy = PermissionPolicy(read=True, write=True)
        first = AgentTask("one", role, "a", ("src",), policy)
        second = AgentTask("two", role, "b", ("src/a.py",), policy)
        self.coordinator.workspace.acquire("one", first.files)
        try:
            with self.assertRaises(WorkspaceConflict):
                self.coordinator.run(second, lambda _task, _checkpoint: "never")
        finally:
            self.coordinator.workspace.release("one")

    def test_budget_is_enforced(self):
        role = AgentRole("tester", ("read",), max_steps=1)
        task = AgentTask("t2", role, "test")

        def worker(_task, checkpoint):
            checkpoint()
            checkpoint()
            return "never"

        with self.assertRaises(AgentBudgetExceeded):
            self.coordinator.run(task, worker)

    def test_cancellation_is_observed(self):
        role = AgentRole("planner", ("read",))
        task = AgentTask("t3", role, "plan")
        self.coordinator.cancel("t3")
        with self.assertRaises(Exception):
            self.coordinator.run(task, lambda _task, _checkpoint: "never")

    def test_shared_context_rejects_credentials(self):
        context = SharedTaskContext()
        context.set("summary", "safe")
        self.assertEqual(context.get("summary"), "safe")
        with self.assertRaises(ValueError):
            context.set("api_token", "secret")


if __name__ == "__main__":
    unittest.main()
