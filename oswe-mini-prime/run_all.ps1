# PowerShell wrapper to run everything
Set-StrictMode -Version Latest
Push-Location -LiteralPath .\Project_A_PreChange
.\setup.sh
.\run_tests.ps1
Copy-Item -Path .\results\results_pre.json -Destination ..\results\results_pre.json -Force
Pop-Location

Push-Location -LiteralPath .\Project_B_PostChange
.\setup.sh
.\run_tests.ps1
Copy-Item -Path .\results\results_post.json -Destination ..\results\results_post.json -Force
Pop-Location

python .\scripts\aggregate_metrics.py results\results_pre.json results\results_post.json
python .\scripts\generate_compare_report.py results\results_pre.json results\results_post.json results\aggregated_metrics.json > compare_report.md

Write-Host 'Done. See compare_report.md and results/'
