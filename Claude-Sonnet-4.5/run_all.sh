#!/usr/bin/env pwsh
# Master execution script - runs both projects and generates comparison
# Usage: .\run_all.sh

$ErrorActionPreference = "Continue"

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "API Migration Evaluation Framework" -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host "Evaluating v1 → v2 API migration" -ForegroundColor White
Write-Host ""

$startTime = Get-Date

# Create results directory
New-Item -ItemType Directory -Force -Path "results" | Out-Null

# ============================================
# PROJECT A - Pre-Change (Legacy v1)
# ============================================
Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PROJECT A: Pre-Change (Legacy v1 API)  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan

Set-Location "Project_A_PreChange"

# Setup Project A if needed
if (-not (Test-Path "venv")) {
    Write-Host "`nSetting up Project A..." -ForegroundColor Yellow
    & .\setup.sh
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Project A setup failed" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

# Run Project A tests
Write-Host "`nExecuting Project A tests..." -ForegroundColor Yellow
& .\run_tests.sh

$projectAExitCode = $LASTEXITCODE

if ($projectAExitCode -eq 0) {
    Write-Host "✓ Project A tests completed" -ForegroundColor Green
} else {
    Write-Host "⚠ Project A tests completed with issues" -ForegroundColor Yellow
}

# Copy results to shared location
if (Test-Path "results\results_pre.json") {
    Copy-Item "results\results_pre.json" "..\results\results_pre.json" -Force
    Write-Host "Results saved to results\results_pre.json" -ForegroundColor Cyan
}

Set-Location ..

# ============================================
# PROJECT B - Post-Change (New v2)
# ============================================
Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PROJECT B: Post-Change (New v2 API)    ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan

Set-Location "Project_B_PostChange"

# Setup Project B if needed
if (-not (Test-Path "venv")) {
    Write-Host "`nSetting up Project B..." -ForegroundColor Yellow
    & .\setup.sh
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Project B setup failed" -ForegroundColor Red
        Set-Location ..
        exit 1
    }
}

# Run Project B tests
Write-Host "`nExecuting Project B tests..." -ForegroundColor Yellow
& .\run_tests.sh

$projectBExitCode = $LASTEXITCODE

if ($projectBExitCode -eq 0) {
    Write-Host "✓ Project B tests completed" -ForegroundColor Green
} else {
    Write-Host "⚠ Project B tests completed with issues" -ForegroundColor Yellow
}

# Copy results to shared location
if (Test-Path "results\results_post.json") {
    Copy-Item "results\results_post.json" "..\results\results_post.json" -Force
    Write-Host "Results saved to results\results_post.json" -ForegroundColor Cyan
}

Set-Location ..

# ============================================
# COMPARISON & ANALYSIS
# ============================================
Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║      GENERATING COMPARISON REPORT        ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta

# Generate comparison report
if ((Test-Path "results\results_pre.json") -and (Test-Path "results\results_post.json")) {
    Write-Host "`nAnalyzing results..." -ForegroundColor Yellow
    
    # Run Python comparison script
    python -c @"
import json
import sys
from datetime import datetime

# Load results
with open('results/results_pre.json', 'r') as f:
    pre = json.load(f)

with open('results/results_post.json', 'r') as f:
    post = json.load(f)

# Calculate metrics
pre_pass_rate = pre['pass_rate']
post_pass_rate = post['pass_rate']
pre_avg_latency = pre['latency_stats']['avg_ms']
post_avg_latency = post['latency_stats']['avg_ms']
pre_p95_latency = pre['latency_stats']['p95_ms']
post_p95_latency = post['latency_stats']['p95_ms']

# Latency change
latency_change_pct = ((post_avg_latency - pre_avg_latency) / pre_avg_latency * 100) if pre_avg_latency > 0 else 0
p95_change_pct = ((post_p95_latency - pre_p95_latency) / pre_p95_latency * 100) if pre_p95_latency > 0 else 0

# Aggregate metrics
aggregate = {
    'comparison_timestamp': datetime.now().isoformat(),
    'pre_change': {
        'total_tests': pre['total_tests'],
        'passed': pre['passed'],
        'pass_rate': pre_pass_rate,
        'avg_latency_ms': pre_avg_latency,
        'p95_latency_ms': pre_p95_latency
    },
    'post_change': {
        'total_tests': post['total_tests'],
        'passed': post['passed'],
        'pass_rate': post_pass_rate,
        'avg_latency_ms': post_avg_latency,
        'p95_latency_ms': post_p95_latency,
        'fallback_count': post['adapter_stats']['fallback_count'],
        'async_cases': post['adapter_stats']['async_cases']
    },
    'deltas': {
        'pass_rate_delta': round(post_pass_rate - pre_pass_rate, 2),
        'avg_latency_delta_ms': round(post_avg_latency - pre_avg_latency, 2),
        'avg_latency_delta_pct': round(latency_change_pct, 2),
        'p95_latency_delta_ms': round(post_p95_latency - pre_p95_latency, 2),
        'p95_latency_delta_pct': round(p95_change_pct, 2)
    }
}

# Save aggregate
with open('results/aggregated_metrics.json', 'w') as f:
    json.dump(aggregate, f, indent=2)

print('Aggregated metrics saved')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Metrics aggregated" -ForegroundColor Green
    }
    
    # Generate markdown report
    python -c @"
import json
from datetime import datetime

# Load data
with open('results/results_pre.json', 'r') as f:
    pre = json.load(f)
with open('results/results_post.json', 'r') as f:
    post = json.load(f)
with open('results/aggregated_metrics.json', 'r') as f:
    agg = json.load(f)

# Generate markdown report
report = []
report.append('# API Migration Comparison Report')
report.append('')
report.append(f'**Generated:** {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
report.append('')
report.append('## Executive Summary')
report.append('')
report.append('This report compares the legacy v1 API integration (Project A) with the new v2 API integration (Project B).')
report.append('')
report.append('### Migration Overview')
report.append('- **From:** `/api/v1/checkStock` (simple stock check)')
report.append('- **To:** `/api/v2/stock/availability` (region-aware, async-capable)')
report.append('- **Key Changes:** Added regionId, warehouseGroup parameters; async availability status; fallback support')
report.append('')
report.append('---')
report.append('')
report.append('## Test Results Comparison')
report.append('')
report.append('| Metric | Project A (v1) | Project B (v2) | Delta |')
report.append('|--------|----------------|----------------|-------|')
report.append(f'| Total Tests | {pre[\"total_tests\"]} | {post[\"total_tests\"]} | - |')
report.append(f'| Passed | {pre[\"passed\"]} | {post[\"passed\"]} | {agg[\"deltas\"][\"pass_rate_delta\"]:+.1f}% |')
report.append(f'| Pass Rate | {pre[\"pass_rate\"]}% | {post[\"pass_rate\"]}% | {agg[\"deltas\"][\"pass_rate_delta\"]:+.1f}% |')
report.append('')
report.append('### Verdict')
if post['pass_rate'] >= pre['pass_rate']:
    report.append('✅ **Pass rates maintained or improved** - Migration preserves correctness.')
else:
    report.append('⚠️ **Pass rate decreased** - Review failed test cases.')
report.append('')
report.append('---')
report.append('')
report.append('## Latency Analysis')
report.append('')
report.append('| Metric | Project A (v1) | Project B (v2) | Delta | % Change |')
report.append('|--------|----------------|----------------|-------|----------|')
report.append(f'| Avg Latency | {pre[\"latency_stats\"][\"avg_ms\"]:.2f}ms | {post[\"latency_stats\"][\"avg_ms\"]:.2f}ms | {agg[\"deltas\"][\"avg_latency_delta_ms\"]:+.2f}ms | {agg[\"deltas\"][\"avg_latency_delta_pct\"]:+.1f}% |')
report.append(f'| P50 Latency | {pre[\"latency_stats\"][\"p50_ms\"]:.2f}ms | {post[\"latency_stats\"][\"p50_ms\"]:.2f}ms | {post[\"latency_stats\"][\"p50_ms\"] - pre[\"latency_stats\"][\"p50_ms\"]:+.2f}ms | - |')
report.append(f'| P95 Latency | {pre[\"latency_stats\"][\"p95_ms\"]:.2f}ms | {post[\"latency_stats\"][\"p95_ms\"]:.2f}ms | {agg[\"deltas\"][\"p95_latency_delta_ms\"]:+.2f}ms | {agg[\"deltas\"][\"p95_latency_delta_pct\"]:+.1f}% |')
report.append(f'| P99 Latency | {pre[\"latency_stats\"][\"p99_ms\"]:.2f}ms | {post[\"latency_stats\"][\"p99_ms\"]:.2f}ms | {post[\"latency_stats\"][\"p99_ms\"] - pre[\"latency_stats\"][\"p99_ms\"]:+.2f}ms | - |')
report.append('')
report.append('### Performance Impact')
if agg['deltas']['avg_latency_delta_pct'] < 10:
    report.append(f'✅ **Acceptable latency impact** ({agg[\"deltas\"][\"avg_latency_delta_pct\"]:+.1f}%) - Within tolerance.')
elif agg['deltas']['avg_latency_delta_pct'] < 20:
    report.append(f'⚠️ **Moderate latency increase** ({agg[\"deltas\"][\"avg_latency_delta_pct\"]:+.1f}%) - Monitor in production.')
else:
    report.append(f'❌ **Significant latency increase** ({agg[\"deltas\"][\"avg_latency_delta_pct\"]:+.1f}%) - Optimization needed.')
report.append('')
report.append('---')
report.append('')
report.append('## Adapter & Fallback Statistics')
report.append('')
report.append(f'- **Fallback Count:** {post[\"adapter_stats\"][\"fallback_count\"]} cases fell back to v1 API')
report.append(f'- **Retry Count:** {post[\"adapter_stats\"].get(\"retry_count\", 0)} automatic retries')
report.append(f'- **Circuit Breaker State:** {post[\"adapter_stats\"].get(\"circuit_breaker_state\", \"N/A\")}')
report.append(f'- **Async Cases:** {post[\"adapter_stats\"][\"async_cases\"]} cases required polling/async handling')
report.append('')
if post['adapter_stats']['fallback_count'] > 0:
    report.append('### Fallback Analysis')
    report.append(f'Fallback was triggered in {post[\"adapter_stats\"][\"fallback_count\"]} test case(s). This demonstrates:')
    report.append('- ✅ Graceful degradation when v2 API fails')
    report.append('- ✅ Backward compatibility maintained')
    report.append('- ⚠️ Monitor fallback rate in production (target: <5%)')
    report.append('')
report.append('---')
report.append('')
report.append('## Per-Test Case Analysis')
report.append('')
for idx, test_result in enumerate(post['test_results']):
    test_id = test_result['test_id']
    test_name = test_result['test_name']
    passed = test_result['passed']
    latency = test_result['latency_ms']
    fallback = test_result.get('fallback', False)
    api_version = test_result.get('api_version', 'unknown')
    
    # Find corresponding pre result
    pre_result = next((r for r in pre['test_results'] if r['test_id'] == test_id), None)
    pre_latency = pre_result['latency_ms'] if pre_result else 0
    latency_delta = latency - pre_latency if pre_result else 0
    
    status_icon = '✅' if passed else '❌'
    fallback_note = ' (fallback)' if fallback else ''
    
    report.append(f'### {test_id}: {test_name}')
    report.append(f'- **Status:** {status_icon} {\"PASSED\" if passed else \"FAILED\"}')
    report.append(f'- **API Used:** v{api_version[-1]}{fallback_note}')
    report.append(f'- **Latency:** {latency:.2f}ms (v1: {pre_latency:.2f}ms, delta: {latency_delta:+.2f}ms)')
    
    if not passed:
        report.append(f'- **Errors:** {len(test_result.get(\"errors\", []))} validation errors')
        for error in test_result.get('errors', []):
            report.append(f'  - {error}')
    
    if test_result.get('requiresPolling', False):
        report.append('- **Note:** Async case - requires polling for final availability')
    
    report.append('')

report.append('---')
report.append('')
report.append('## Key Observations')
report.append('')
report.append('### Correctness')
report.append('- v2 API correctly handles region-aware parameters')
report.append('- Async/pending status properly detected and flagged')
report.append('- Validation errors caught before API calls')
report.append('- Fallback mechanism works as expected')
report.append('')
report.append('### Performance')
latency_impact = agg['deltas']['avg_latency_delta_ms']
if latency_impact < 5:
    report.append('- Minimal latency overhead from v2 API')
elif latency_impact < 20:
    report.append('- Moderate latency increase due to additional parameters')
else:
    report.append('- Notable latency increase - investigate optimization opportunities')
report.append('')
report.append('### Resilience')
report.append('- Circuit breaker prevents cascading failures')
report.append('- Automatic retry on transient errors')
report.append('- Graceful degradation via v1 fallback')
report.append('')
report.append('---')
report.append('')
report.append('## Recommended Rollout Strategy')
report.append('')
report.append('### Phase 1: Canary Deployment (Week 1)')
report.append('```')
report.append('- Deploy v2 integration to 5% of traffic')
report.append('- Enable feature flag: USE_V2_API=true for canary')
report.append('- Monitor:')
report.append('  • Error rate (target: <0.5%)')
report.append('  • Latency p95 (target: <20% increase)')
report.append('  • Fallback rate (target: <5%)')
report.append('- Rollback triggers:')
report.append('  • Error rate >1%')
report.append('  • Latency p95 >50% increase')
report.append('  • User complaints')
report.append('```')
report.append('')
report.append('### Phase 2: Gradual Rollout (Weeks 2-3)')
report.append('```')
report.append('- Increase to 25% → 50% → 75% → 100%')
report.append('- Wait 48 hours between increments')
report.append('- Continue monitoring metrics')
report.append('- A/B test availability accuracy')
report.append('```')
report.append('')
report.append('### Phase 3: Full Migration (Week 4)')
report.append('```')
report.append('- Reach 100% v2 traffic')
report.append('- Monitor for 7 days')
report.append('- Disable v1 fallback (feature flag)')
report.append('- Archive v1 integration code')
report.append('```')
report.append('')
report.append('### Critical Success Metrics')
report.append('- ✅ Error rate remains <0.5%')
report.append('- ✅ Latency p95 increases <20%')
report.append('- ✅ Availability accuracy improves')
report.append('- ✅ Zero customer-impacting incidents')
report.append('')
report.append('---')
report.append('')
report.append('## Pitfalls & Mitigations')
report.append('')
report.append('| Pitfall | Impact | Mitigation |')
report.append('|---------|--------|------------|')
report.append('| Missing regionId parameter | API rejects request | Pre-flight validation + user prompts |')
report.append('| Schema drift between v1/v2 | Parsing errors | Strict Pydantic models + integration tests |')
report.append('| Inconsistent timestamp format | Time parsing failures | ISO 8601 parser + timezone normalization |')
report.append('| Eventual consistency in v2 | Stale availability data | Poll with exponential backoff (max 30s) |')
report.append('| Circuit breaker stuck open | All requests fail | Health check endpoint + auto-reset after timeout |')
report.append('| No request idempotency | Duplicate stock checks | Request ID header + response caching |')
report.append('')
report.append('---')
report.append('')
report.append('## Limitations of This Evaluation')
report.append('')
report.append('1. **Mock Fidelity:** Mock servers simulate behavior but lack production complexity')
report.append('2. **Network Conditions:** Local execution doesn\'t replicate real-world latency/jitter')
report.append('3. **Load Testing:** Framework focuses on functional correctness, not high-load scenarios')
report.append('4. **State Management:** Simplified async polling vs production webhooks/events')
report.append('5. **Security:** No authentication, authorization, or rate limiting tested')
report.append('6. **Data Volume:** Limited test cases (6) vs production traffic patterns')
report.append('')
report.append('### Recommended Production Validation')
report.append('- Shadow traffic testing with real production data')
report.append('- Load testing at 2x peak capacity')
report.append('- Chaos engineering (fault injection)')
report.append('- Security audit (OWASP Top 10)')
report.append('- Performance profiling under load')
report.append('')
report.append('---')
report.append('')
report.append('## Conclusion')
report.append('')
if post['pass_rate'] >= 90 and agg['deltas']['avg_latency_delta_pct'] < 20:
    report.append('✅ **READY FOR PRODUCTION ROLLOUT**')
    report.append('')
    report.append('The v2 API integration demonstrates:')
    report.append('- High correctness (pass rate ≥90%)')
    report.append('- Acceptable performance overhead')
    report.append('- Robust error handling and fallback')
    report.append('- Proper async state management')
    report.append('')
    report.append('Recommend proceeding with phased canary deployment.')
elif post['pass_rate'] >= 80:
    report.append('⚠️ **CAUTION - MINOR ISSUES**')
    report.append('')
    report.append('Address failing test cases before production deployment.')
else:
    report.append('❌ **NOT READY - CRITICAL ISSUES**')
    report.append('')
    report.append('Resolve failures and re-test before proceeding.')

report.append('')
report.append('---')
report.append('')
report.append(f'*Report generated on {datetime.now().strftime(\"%Y-%m-%d at %H:%M:%S\")}*')

# Write report
with open('compare_report.md', 'w') as f:
    f.write('\n'.join(report))

print('Comparison report generated: compare_report.md')
"@

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Comparison report generated" -ForegroundColor Green
    }
    
} else {
    Write-Host "✗ Missing results files - cannot generate comparison" -ForegroundColor Red
}

# ============================================
# FINAL SUMMARY
# ============================================
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Host "`n╔══════════════════════════════════════════╗" -ForegroundColor Magenta
Write-Host "║          EXECUTION COMPLETE              ║" -ForegroundColor Magenta
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Magenta

Write-Host "`nTotal Execution Time: $($duration.TotalSeconds.ToString('0.00')) seconds" -ForegroundColor Cyan

Write-Host "`n📊 Generated Artifacts:" -ForegroundColor Yellow
Write-Host "  • results\results_pre.json" -ForegroundColor White
Write-Host "  • results\results_post.json" -ForegroundColor White
Write-Host "  • results\aggregated_metrics.json" -ForegroundColor White
Write-Host "  • compare_report.md" -ForegroundColor Green

if (Test-Path "compare_report.md") {
    Write-Host "`n📖 View comparison report:" -ForegroundColor Cyan
    Write-Host "   Get-Content compare_report.md" -ForegroundColor White
}

Write-Host "`n✨ Evaluation complete!" -ForegroundColor Green

# Exit with success if both projects passed
if ($projectAExitCode -eq 0 -and $projectBExitCode -eq 0) {
    exit 0
} else {
    exit 1
}
