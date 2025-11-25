#!/usr/bin/env bash
set -euo pipefail
mkdir -p logs results
python -m pip install --user -r requirements.txt || true
python tests/test_pre_change.py | tee logs/log_pre.txt
