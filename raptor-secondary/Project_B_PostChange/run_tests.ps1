$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venv = Join-Path $root ".venv"
python -m venv $venv
& "$venv\Scripts\pip.exe" install -r (Join-Path $root "requirements.txt")
# Include repo root for fallback mock imports
$repoRoot = Split-Path -Parent $root
$env:PYTHONPATH = "$root;$repoRoot;" + ($env:PYTHONPATH)
$testRunner = Join-Path (Join-Path $root "tests") "run_post_tests.py"
& "$venv\Scripts\python.exe" $testRunner
