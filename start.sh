#!/usr/bin/env bash
set -e

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ -f "$ROOT/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    . "$ROOT/.venv/bin/activate"
fi

exec python "$ROOT/main.py" "$@"
