# Platform Integration Matrix

| Platform | Automated CI | Runtime/CLI coverage | Native interactive coverage |
|---|---|---|---|
| Linux | PASS target via GitHub Actions | PASS | NOT TESTED for Android/Termux-specific interaction |
| macOS | PASS target via GitHub Actions | PASS | NOT TESTED |
| Windows | PASS target via GitHub Actions | PASS | NOT TESTED |
| Termux/Android | NOT TESTED in repository CI | Deterministic runtime contract only | NOT TESTED without a native Android terminal |

## Scope

The cross-platform CI job uses Python 3.12 on Linux, macOS, and Windows. It installs the clean package, compiles the source tree, runs the platform integration and TUI non-interactive tests, and performs a CLI smoke test.

Termux/Android remains a first-class target, but this repository CI matrix does not claim to execute Android. Native Termux acceptance is recorded separately when an actual Termux terminal is available.

Platform-specific tests use native OS conventions through `core.runtime`; they do not substitute a different OS and label it as the target platform.