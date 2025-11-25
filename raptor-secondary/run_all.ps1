$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Project A
$projA = Join-Path $root "Project_A_PreChange"
& (Join-Path $projA "run_tests.ps1")

# Project B
$projB = Join-Path $root "Project_B_PostChange"
& (Join-Path $projB "run_tests.ps1")

# Collect results
$resultsRoot = Join-Path $root "results"
New-Item -ItemType Directory -Force -Path $resultsRoot | Out-Null
$projAResults = Join-Path (Join-Path $projA "results") "results_pre.json"
$projBResults = Join-Path (Join-Path $projB "results") "results_post.json"
Copy-Item $projAResults $resultsRoot -Force
Copy-Item $projBResults $resultsRoot -Force

# Aggregate
python (Join-Path $root "aggregate_results.py")

Write-Host "Report generated at $(Join-Path $root 'compare_report.md')"
