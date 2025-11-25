#!/usr/bin/env bash
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)
source "$ROOT/setup.sh"

python -m pytest -q --maxfail=1 tests/test_post_change.py
