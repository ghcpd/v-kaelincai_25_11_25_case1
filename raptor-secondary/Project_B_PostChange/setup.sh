#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VENV_DIR="$ROOT_DIR/.venv"
python -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install -r "$ROOT_DIR/requirements.txt"
echo "Venv ready at $VENV_DIR"
