#!/usr/bin/env bash
set -euo pipefail

ROOT=$(pwd)
mkdir -p results

echo "Running Project A (pre-change)..."
pushd Project_A_PreChange
bash run_tests.sh
popd
cp Project_A_PreChange/results/results_pre.json results/results_pre.json

echo "Running Project B (post-change)..."
pushd Project_B_PostChange
bash run_tests.sh
popd
cp Project_B_PostChange/results/results_post.json results/results_post.json

echo "Aggregating results and producing compare_report.md"
python - <<'PY'
import json, sys
pre = json.load(open('results/results_pre.json'))
post = json.load(open('results/results_post.json'))
out = {'pre': pre, 'post': post}
json.dump(out, open('results/aggregated_metrics.json','w'), indent=2)
print('Wrote results/aggregated_metrics.json')
PY

python scripts/generate_report.py results/results_pre.json results/results_post.json > compare_report.md || true

echo "Done. compare_report.md is created."
