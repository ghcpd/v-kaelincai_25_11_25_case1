#!/usr/bin/env bash
set -e
ROOT=$(cd "$(dirname "$0")" && pwd)

# Run Project A tests
pushd Project_A_PreChange
bash setup.sh || true
bash run_tests.sh
cp results/results_pre.json ../results/results_pre.json || true
popd

# Run Project B tests
pushd Project_B_PostChange
bash setup.sh || true
bash run_tests.sh
cp results/results_post.json ../results/results_post.json || true
popd

# Aggregate
python scripts/aggregate_metrics.py results/results_pre.json results/results_post.json
python scripts/generate_compare_report.py results/results_pre.json results/results_post.json results/aggregated_metrics.json > compare_report.md

echo 'Done. See compare_report.md and results/'
