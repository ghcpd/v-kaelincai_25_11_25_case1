$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venv = Join-Path $root ".venv"

python -m venv $venv
& "$venv\Scripts\pip.exe" install -r (Join-Path $root "requirements.txt")
$env:PYTHONPATH = "$root;" + ($env:PYTHONPATH)
$testRunner = Join-Path (Join-Path $root "tests") "run_pre_tests.py"
& "$venv\Scripts\python.exe" $testRunner
