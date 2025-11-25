#!/usr/bin/env pwsh
# Test execution script for Project B (Post-Change)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Project B Tests (Post-Change)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Run setup.sh first." -ForegroundColor Red
    exit 1
}

# Start mock API v2 server in background
Write-Host "`nStarting mock API v2 server..." -ForegroundColor Yellow
$mockV2Job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\venv\Scripts\Activate.ps1
    python mocks\mock_api_v2.py
}

# Start mock API v1 server for fallback testing
Write-Host "Starting mock API v1 server (for fallback)..." -ForegroundColor Yellow
$mockV1Job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\venv\Scripts\Activate.ps1
    
    # Use v1 mock from Project A if available
    if (Test-Path "..\Project_A_PreChange\mocks\mock_api_v1.py") {
        python ..\Project_A_PreChange\mocks\mock_api_v1.py
    } else {
        # Simple fallback mock
        python -c @"
from flask import Flask, request, jsonify
app = Flask(__name__)

STOCK_DB = {
    'ABC123': {'available': True, 'stock': 12},
    'XYZ789': {'available': False, 'stock': 0},
    'DEF456': {'available': True, 'stock': 15},
    'GHI999': {'available': True, 'stock': 8},
    'JKL111': {'available': True, 'stock': 5},
    'MNO222': {'available': True, 'stock': 3}
}

@app.route('/api/v1/checkStock', methods=['POST'])
def check_stock():
    data = request.get_json()
    sku = data.get('sku')
    stock_info = STOCK_DB.get(sku, {'available': False, 'stock': 0})
    return jsonify({'sku': sku, 'available': stock_info['available'], 'stock': stock_info['stock']}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'version': 'v1'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
"@
    }
}

# Wait for servers to start
Write-Host "Waiting for servers to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

# Check if v2 server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5002/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Mock API v2 server is ready" -ForegroundColor Green
} catch {
    Write-Host "✗ Failed to start mock API v2 server" -ForegroundColor Red
    Stop-Job -Job $mockV2Job
    Remove-Job -Job $mockV2Job
    Stop-Job -Job $mockV1Job
    Remove-Job -Job $mockV1Job
    exit 1
}

# Check if v1 server is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5001/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "✓ Mock API v1 server is ready (fallback)" -ForegroundColor Green
} catch {
    Write-Host "⚠ Warning: v1 server not available (fallback tests may fail)" -ForegroundColor Yellow
}

# Run tests
Write-Host "`nRunning test suite..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$logFile = "logs\log_post_$timestamp.txt"

python tests\test_post_change.py 2>&1 | Tee-Object -FilePath $logFile

$testExitCode = $LASTEXITCODE

# Stop mock servers
Write-Host "`nStopping mock API servers..." -ForegroundColor Yellow
Stop-Job -Job $mockV2Job
Remove-Job -Job $mockV2Job
Stop-Job -Job $mockV1Job
Remove-Job -Job $mockV1Job

# Copy latest log
Copy-Item $logFile "logs\log_post.txt" -Force

# Display results
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path "results\results_post.json") {
    $results = Get-Content "results\results_post.json" | ConvertFrom-Json
    
    Write-Host "`nResults Summary:" -ForegroundColor Yellow
    Write-Host "  Total Tests: $($results.total_tests)"
    Write-Host "  Passed: $($results.passed)" -ForegroundColor Green
    Write-Host "  Failed: $($results.failed)" -ForegroundColor $(if ($results.failed -gt 0) { "Red" } else { "Green" })
    Write-Host "  Pass Rate: $($results.pass_rate)%"
    Write-Host "  Avg Latency: $($results.latency_stats.avg_ms)ms"
    Write-Host "  P95 Latency: $($results.latency_stats.p95_ms)ms"
    Write-Host "  Fallback Count: $($results.adapter_stats.fallback_count)"
    Write-Host "  Async Cases: $($results.adapter_stats.async_cases)"
    
    Write-Host "`nLog: $logFile" -ForegroundColor Cyan
    Write-Host "Results: results\results_post.json" -ForegroundColor Cyan
} else {
    Write-Host "Results file not found." -ForegroundColor Red
}

exit $testExitCode
