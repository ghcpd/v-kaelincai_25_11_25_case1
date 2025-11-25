#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Run Project A tests
pushd "$ROOT_DIR/Project_A_PreChange" >/dev/null
./run_tests.sh
popd >/dev/null

# Run Project B tests
pushd "$ROOT_DIR/Project_B_PostChange" >/dev/null
./run_tests.sh
popd >/dev/null

# Collect results
mkdir -p "$ROOT_DIR/results"
cp "$ROOT_DIR/Project_A_PreChange/results/results_pre.json" "$ROOT_DIR/results/results_pre.json"
cp "$ROOT_DIR/Project_B_PostChange/results/results_post.json" "$ROOT_DIR/results/results_post.json"

# Aggregate
python "$ROOT_DIR/aggregate_results.py"

echo "Report generated at $ROOT_DIR/compare_report.md"
