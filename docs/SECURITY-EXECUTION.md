# Sandboxed execution and permissions

YasinCoder treats model output as untrusted input. Tool calls are explicit, workspace-confined, permission-aware, time-bounded, and observable.

## Capability policy

The runtime exposes six capabilities:

- `read` — inspect files/workspace/search.
- `write` — mutate files; disabled by default and required in addition to `apply=true`.
- `execute` — run ordinary local commands.
- `network` — run commands classified as network-capable.
- `git` — run Git commands.
- `admin` — run administrative commands.

Read is enabled by default. All side-effectful capabilities are denied by default.

## Workspace confinement

All file paths are resolved beneath the configured workspace. Absolute paths are also checked. Symlink resolution is performed before the containment check, so a link pointing outside the workspace is rejected.

## Process controls

Command execution:

- runs with the workspace as its working directory;
- receives no interactive stdin;
- starts in a separate process group;
- has a configurable timeout capped at one hour;
- terminates the process group on timeout and escalates to `SIGKILL` if required.

## Approval model

A proposed file mutation is dry-run by default. Applying it requires both `apply=true` and the `write` capability. Command execution and Git operations likewise require their corresponding capabilities. This keeps model-generated plans separate from side effects.

## Auditability

Every tool result contains a structured `audit` record with the tool, requested capability, and success state. Higher-level UI/session logging can persist these records without exposing secrets.

## Network and admin boundaries

Network-capable and administrative commands are classified separately from ordinary execution. A generic `execute` permission does not grant either capability. The classification is intentionally conservative and can be extended as new tools are added.

## Security boundary

This layer is a safety boundary, not a full operating-system sandbox. For hostile multi-tenant workloads, run YasinCoder inside an OS/container sandbox with restricted filesystem, user, network, and resource permissions in addition to this policy.
