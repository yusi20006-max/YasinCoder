# YasinCoder Terminal UI

The Terminal UI (TUI) is the visual command center for YasinCoder in Termux and normal interactive terminals.

## Launch

```bash
yasincoder tui
```

After installation, the dedicated launcher is also available:

```bash
yasincoder-tui
```

## Navigation

The UI is keyboard-first:

- `1` Dashboard
- `2` New Task
- `3` Projects
- `4` Sessions
- `5` Providers & Models
- `6` Git / Changes
- `7` Tests
- `8` System Status
- `9` Settings
- `q` Quit

The dashboard also provides the main entry point for starting a coding task.

## Real state

The TUI reuses existing YasinCoder interfaces for project information, Git status and model configuration. It deliberately does not manufacture progress counts, provider health, test totals, or Git state. If a subsystem does not currently expose persistent session information, the Sessions screen says so instead of inventing records.

## Termux behavior

The implementation has no third-party UI dependency. This keeps installation and startup small for native ARM64 Termux. The terminal size is read on each screen, content is clipped to the available width, and the interface uses a minimum layout suitable for narrow displays. ANSI color is disabled automatically for redirected output, dumb terminals, or `NO_COLOR`.

## Simple and advanced use

The dashboard is intentionally simple for a user who only wants to describe a coding task. Technical state is available through the Projects, Models, Git, Tests and System screens. The underlying state and security rules are the same; the UI never bypasses provider credential handling or safe Git boundaries.

## Git safety

Git information is read through `GitManager`. The UI does not offer silent reset, force, checkout, or destructive cleanup actions. Conflicts are surfaced explicitly.

## Tests

TUI logic can be tested without an interactive terminal:

```bash
python -m unittest tests.test_tui -v
```

The complete repository suite remains the release gate.
