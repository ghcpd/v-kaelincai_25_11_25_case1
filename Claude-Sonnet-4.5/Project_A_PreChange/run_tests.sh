#!/usr/bin/env pwsh
# Test execution script for Project A (Pre-Change)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Project A Tests (Pre-Change)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Run setup.sh first." -ForegroundColor Red
    exit 1
}

# Start mock API server in background
Write-Host "`nStarting mock API v1 server..." -ForegroundColor Yellow
$mockJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\venv\Scripts\Activate.ps1
    python mocks\mock_api_v1.py
}

# Wait for server to start
Write-Host "Waiting for server to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Check if server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Mock API v1 server is ready" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start mock API server" -ForegroundColor Red
    Stop-Job -Job $mockJob
    Remove-Job -Job $mockJob
    exit 1
}

# Run tests
Write-Host "`nRunning test suite..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = "logs\log_pre_$timestamp.txt"

python tests\test_pre_change.py 2>&1 | Tee-Object -FilePath $logFile

$testExitCode = $LASTEXITCODE

# Stop mock server
Write-Host "`nStopping mock API server..." -ForegroundColor Yellow
Stop-Job -Job $mockJob
Remove-Job -Job $mockJob

# Copy latest log
Copy-Item $logFile "logs\log_pre.txt" -Force

# Display results
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path "results\results_pre.json") {
    $results = Get-Content "results\results_pre.json" | ConvertFrom-Json
    
    Write-Host "`nResults Summary:" -ForegroundColor Yellow
    Write-Host "  Total Tests: $($results.total_tests)"
    Write-Host "  Passed: $($results.passed)" -ForegroundColor Green
    Write-Host "  Failed: $($results.failed)" -ForegroundColor $(if ($results.failed -gt 0) { "Red" } else { "Green" })
    Write-Host "  Pass Rate: $($results.pass_rate)%"
    Write-Host "  Avg Latency: $($results.latency_stats.avg_ms)ms"
    Write-Host "  P95 Latency: $($results.latency_stats.p95_ms)ms"
    
    Write-Host "`nLog: $logFile" -ForegroundColor Cyan
    Write-Host "Results: results\results_pre.json" -ForegroundColor Cyan
} else {
    Write-Host "Results file not found." -ForegroundColor Red
}

exit $testExitCode
