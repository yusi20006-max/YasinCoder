# GitHub Mode workflow

The integration is composed of independent capabilities and services:

`Issue → Branch → Code/Test → Commit → Push → PR → CI → explicit Merge`

The orchestration layer records state and refuses to cross unsafe gates. It does not grant permissions, store credentials, or merge automatically.

## Merge gate

A merge requires all of the following:

1. a valid Issue-derived workflow state;
2. a commit and Pull Request;
3. successful CI reported by GitHub Actions;
4. the `merge` capability explicitly enabled;
5. an explicit `approved=True` decision supplied by the caller.

This makes merge an intentional, auditable operation rather than an incidental side effect of automation.

## Failure handling

A failed CI run leaves the workflow before merge. A caller can fix code, create a new commit, push it, and re-run CI verification. No automatic retry loop can silently bypass the CI or approval gates.
