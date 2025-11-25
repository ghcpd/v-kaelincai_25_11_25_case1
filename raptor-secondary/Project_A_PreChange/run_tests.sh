#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR="$ROOT_DIR/.venv"

python -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install -r "$ROOT_DIR/requirements.txt"
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
python "$ROOT_DIR/tests/run_pre_tests.py"
