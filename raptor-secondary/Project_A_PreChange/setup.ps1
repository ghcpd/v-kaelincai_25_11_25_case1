$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venv = Join-Path $root ".venv"
python -m venv $venv
& "$venv\Scripts\pip.exe" install -r (Join-Path $root "requirements.txt")
Write-Host "Venv ready at $venv"
