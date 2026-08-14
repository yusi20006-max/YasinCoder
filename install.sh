#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

printf '%s\n' '=============================================' ' YasinCoder Installer' '============================================='

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON_BIN is required. Install Python 3.10+ and rerun."
  exit 1
fi

"$PYTHON_BIN" - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("ERROR: Python 3.10+ is required.")
print(f"Python OK: {sys.version.split()[0]}")
PY

if command -v git >/dev/null 2>&1; then
  echo "Git OK: $(git --version)"
else
  echo "WARNING: Git is not installed. Repository operations will be unavailable."
fi

"$PYTHON_BIN" "$ROOT/scripts/bootstrap.py" doctor || true

echo
echo "Starting first-run configuration..."
"$PYTHON_BIN" "$ROOT/scripts/bootstrap.py" configure

echo
echo "Installation/bootstrap complete."
echo "External runtime state: ${YASIN_CONFIG_DIR:-$HOME/.config/yasin-coder}"
echo "Run: $PYTHON_BIN scripts/bootstrap.py doctor"
echo "Reset external configuration: $PYTHON_BIN scripts/bootstrap.py reset"
