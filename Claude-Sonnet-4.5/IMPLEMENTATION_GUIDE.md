# API Change Evaluation: Detailed Implementation Guide

## Overview

This document provides comprehensive implementation details for the API migration evaluation framework.

---

## Test Scenario Description

### API Change Scenario

**Business Context:**  
A commerce platform is migrating from a simple stock checking API to a sophisticated, region-aware availability system. The new API supports multi-region inventory with warehouse groups and asynchronous availability updates.

**Technical Migration:**
- **Old API (v1):** `/api/v1/checkStock`
  - Input: `{sku: "ABC123"}`
  - Output: `{sku: "ABC123", available: true, stock: 12}`
  - Simple, synchronous, no region awareness

- **New API (v2):** `/api/v2/stock/availability`
  - Input: `{sku: "ABC123", regionId: "ap-sg-1", warehouseGroup: "WG-2", quantity: 5}`
  - Output: `{sku: "ABC123", available: true, quantity: 12, availabilityStatus: "confirmed", syncTimestamp: "2025-11-25T12:00:00Z", regionId: "ap-sg-1", warehouseGroup: "WG-2"}`
  - Region-aware, supports async states, richer metadata

### Capability Under Test

The evaluation tests AI models' ability to:
1. **Implement Parameter Migration:** Correctly add regionId and warehouseGroup parameters
2. **Handle Schema Changes:** Parse new response fields (availabilityStatus, syncTimestamp)
3. **Manage Async States:** Detect and handle "pending" availability requiring polling
4. **Implement Fallback:** Gracefully degrade to v1 when v2 fails
5. **Validate Inputs:** Catch missing required parameters before API calls
6. **Monitor Performance:** Track latency and error rates

---

## Test Data Generation

### Test Cases (6 scenarios)

#### TC001: Normal Case - Confirmed Availability
- **Purpose:** Validate basic v2 API integration with immediate confirmation
- **Input:** `{sku: "ABC123", regionId: "ap-sg-1", warehouseGroup: "WG-2", quantity: 5}`
- **Expected Output:** `{available: true, quantity: 12, note: "confirmed"}`
- **Pass Criteria:** Status 200, correct availability decision

#### TC002: Boundary Case - Zero Quantity
- **Purpose:** Test edge case of out-of-stock item
- **Input:** `{sku: "XYZ789", regionId: "us-east-1", warehouseGroup: "WG-1", quantity: 1}`
- **Expected Output:** `{available: false, quantity: 0, note: "confirmed"}`
- **Pass Criteria:** Status 200, correctly identifies unavailability

#### TC003: Asynchronous Case - Pending Availability
- **Purpose:** Validate async handling when status is "pending"
- **Input:** `{sku: "DEF456", regionId: "eu-west-1", warehouseGroup: "WG-3", quantity: 10}`
- **Expected Output:** `{available: true, quantity: 15, note: "pending_sync", requiresPolling: true}`
- **Pass Criteria:** Status 200, async flag set, estimated sync time present

#### TC004: Invalid Input - Missing regionId
- **Purpose:** Test validation logic for missing required parameter
- **Input:** `{sku: "GHI999", warehouseGroup: "WG-1", quantity: 3}` (no regionId)
- **Expected Output:** `{available: false, note: "validation_error", fallback: true}`
- **Pass Criteria:** Validation error caught, fallback to v1 triggered

#### TC005: Error Case - Service Timeout/500
- **Purpose:** Test resilience when v2 API fails
- **Input:** `{sku: "JKL111", regionId: "ap-ne-1", warehouseGroup: "WG-5", quantity: 2}`
- **Expected Output:** `{available: false, note: "service_error", fallback: true, retryable: true}`
- **Pass Criteria:** Error detected, retry attempted, fallback successful

#### TC006: Boundary Case - At Reserve Threshold
- **Purpose:** Test edge case of stock exactly at threshold
- **Input:** `{sku: "MNO222", regionId: "us-west-2", warehouseGroup: "WG-2", quantity: 3}`
- **Expected Output:** `{available: true, quantity: 3, note: "confirmed_at_threshold"}`
- **Pass Criteria:** Status 200, threshold flag detected

### Test Data Format

All test cases are stored in `test_data.json` with the structure:
```json
{
  "test_id": "TC001",
  "name": "Human-readable name",
  "description": "What this test validates",
  "input": { /* Input parameters */ },
  "expected_v1_response": { /* Mock v1 response */ },
  "expected_v2_response": { /* Mock v2 response */ },
  "expected_outcome": { /* Final expected result */ },
  "expected_status": 200
}
```

---

## Reproducible Environment

### Requirements

**Python Dependencies (requirements.txt):**
- Flask 3.0.0 - Mock API servers
- requests 2.31.0 - HTTP client
- Werkzeug 3.0.1 - WSGI utilities

**System Requirements:**
- Python 3.8+
- PowerShell 5.1+ (Windows)
- 256MB RAM minimum
- Network ports: 5001 (v1 mock), 5002 (v2 mock)

### Environment Setup

**Project A (Pre-Change):**
```powershell
cd Project_A_PreChange
.\setup.sh      # Creates venv, installs deps, copies test data
```

**Project B (Post-Change):**
```powershell
cd Project_B_PostChange
.\setup.sh      # Creates venv, installs deps, copies test data
```

### Configuration

**Mock Server Ports:**
- v1 API: `http://localhost:5001`
- v2 API: `http://localhost:5002`

**Timeouts:**
- API request timeout: 5 seconds
- Server startup wait: 3-4 seconds

**Feature Flags:**
- `use_adapter=True` - Enable adapter pattern in Project B
- `enable_fallback=True` - Allow fallback to v1

---

## Test Code Structure

### Project A (Pre-Change)

**cart_service_v1.py:**
- Simple integration with `/api/v1/checkStock`
- Basic error handling
- Synchronous flow only
- Returns: `{available, quantity, note, status_code, latency_ms, api_version}`

**mock_api_v1.py:**
- Flask server on port 5001
- Simulates v1 stock database
- Returns simple stock responses
- Simulates 500 error for SKU "JKL111"

**test_pre_change.py:**
- Unittest-based test harness
- Loads test cases from `test_data.json`
- Validates expected_v1_response fields
- Calculates latency statistics (avg, p50, p95, p99)
- Outputs `results_pre.json`

### Project B (Post-Change)

**cart_service_v2.py:**
- Integration with `/api/v2/stock/availability`
- Parameter validation (regionId, warehouseGroup)
- Async state detection (availabilityStatus: "pending")
- Uses adapter for fallback
- Returns: `{available, quantity, note, status_code, latency_ms, api_version, availabilityStatus, syncTimestamp, requiresPolling, fallback}`

**adapter.py:**
- **Validation Layer:** Pre-flight parameter checks
- **Circuit Breaker:** Tracks failures, opens after 3 consecutive failures
- **Retry Logic:** One automatic retry on 5xx errors
- **Fallback:** Calls v1 API when v2 fails or validation fails
- **Statistics:** Tracks fallback_count, retry_count, circuit_breaker_state

**mock_api_v2.py:**
- Flask server on port 5002
- Region-aware stock database
- Returns v2-format responses with async fields
- Simulates "pending" status for SKU "DEF456"
- Simulates 500 error for SKU "JKL111"
- Returns 400 for missing parameters

**test_post_change.py:**
- Similar to test_pre_change.py but validates v2 responses
- Checks async handling (requiresPolling flag)
- Validates fallback behavior
- Tracks adapter statistics
- Outputs `results_post.json`

---

## Execution Scripts

### Per-Project Execution

**Project A: run_tests.sh**
1. Activate virtual environment
2. Start mock v1 server (background job)
3. Wait for server health check
4. Run test suite (`test_pre_change.py`)
5. Capture logs to `logs/log_pre_*.txt`
6. Stop mock server
7. Display summary

**Project B: run_tests.sh**
1. Activate virtual environment
2. Start mock v2 server (background job)
3. Start mock v1 server (for fallback, background job)
4. Wait for both servers to be healthy
5. Run test suite (`test_post_change.py`)
6. Capture logs to `logs/log_post_*.txt`
7. Stop both mock servers
8. Display summary

### Master Execution: run_all.sh

**Orchestration Flow:**
1. **Setup Phase:**
   - Create shared results directory
   - Run setup.sh for both projects if needed

2. **Project A Execution:**
   - Navigate to Project_A_PreChange
   - Run tests via `run_tests.sh`
   - Copy `results_pre.json` to shared results/

3. **Project B Execution:**
   - Navigate to Project_B_PostChange
   - Run tests via `run_tests.sh`
   - Copy `results_post.json` to shared results/

4. **Comparison Generation:**
   - Load both result files
   - Calculate deltas (pass rate, latency, etc.)
   - Generate `aggregated_metrics.json`
   - Generate `compare_report.md` (markdown report)

5. **Summary Display:**
   - Show execution time
   - List generated artifacts
   - Exit with success if both projects passed

---

## Expected Outputs

### Per-Test Output Format

**results_pre.json / results_post.json:**
```json
{
  "project": "Project_A_PreChange",
  "api_version": "v1",
  "timestamp": "2025-11-25T12:34:56",
  "execution_time_seconds": 3.45,
  "total_tests": 6,
  "passed": 5,
  "failed": 1,
  "pass_rate": 83.33,
  "latency_stats": {
    "avg_ms": 12.45,
    "p50_ms": 10.20,
    "p95_ms": 18.90,
    "p99_ms": 20.10,
    "min_ms": 8.50,
    "max_ms": 22.30
  },
  "adapter_stats": { /* Only in results_post.json */
    "fallback_count": 2,
    "retry_count": 1,
    "circuit_breaker_state": "CLOSED",
    "async_cases": 1
  },
  "test_results": [
    {
      "test_id": "TC001",
      "test_name": "Normal case - Confirmed availability",
      "passed": true,
      "errors": [],
      "result": { /* Full API response */ },
      "expected": { /* Expected outcome */ },
      "latency_ms": 10.20
    }
  ]
}
```

### Aggregated Metrics

**aggregated_metrics.json:**
```json
{
  "comparison_timestamp": "2025-11-25T12:35:00",
  "pre_change": {
    "total_tests": 6,
    "passed": 5,
    "pass_rate": 83.33,
    "avg_latency_ms": 12.45,
    "p95_latency_ms": 18.90
  },
  "post_change": {
    "total_tests": 6,
    "passed": 6,
    "pass_rate": 100.0,
    "avg_latency_ms": 15.20,
    "p95_latency_ms": 22.50,
    "fallback_count": 2,
    "async_cases": 1
  },
  "deltas": {
    "pass_rate_delta": +16.67,
    "avg_latency_delta_ms": +2.75,
    "avg_latency_delta_pct": +22.09,
    "p95_latency_delta_ms": +3.60,
    "p95_latency_delta_pct": +19.05
  }
}
```

### Comparison Report

**compare_report.md:**
- Executive summary
- Test results table (v1 vs v2)
- Latency analysis with delta calculations
- Adapter/fallback statistics
- Per-test case breakdown
- Performance verdict (✅/⚠️/❌)
- Rollout recommendations (3-phase strategy)
- Pitfalls & mitigations table
- Limitations & production validation checklist
- Final go/no-go conclusion

---

## Documentation & Explanation

### Per-Test Case Explanations

**TC001 (Normal Case):**
- **Validates:** Basic v2 parameter mapping (sku → sku, + regionId, + warehouseGroup)
- **Verifies:** Immediate "confirmed" status handling
- **Pitfall Check:** Ensures new parameters don't break existing logic

**TC002 (Boundary - Zero Quantity):**
- **Validates:** Correct unavailable detection when quantity = 0
- **Verifies:** Edge case handling at stock boundary
- **Pitfall Check:** Prevents false "available" for out-of-stock items

**TC003 (Async/Pending):**
- **Validates:** Detection of asynchronous availability status
- **Verifies:** `requiresPolling` flag set, estimatedSyncTime present
- **Pitfall Check:** Ensures system doesn't block on pending responses
- **Note:** In production, would implement polling with exponential backoff

**TC004 (Invalid Input):**
- **Validates:** Pre-flight parameter validation
- **Verifies:** Fallback to v1 when regionId missing
- **Pitfall Check:** Prevents 400 errors from reaching API
- **Mitigation:** Adapter catches validation errors and triggers fallback

**TC005 (Service Error):**
- **Validates:** Resilience to v2 API failures (500 errors, timeouts)
- **Verifies:** Retry logic, fallback to v1, error categorization
- **Pitfall Check:** Ensures no user-facing failures on backend issues
- **Mitigation:** Circuit breaker prevents cascade; fallback maintains service

**TC006 (At Threshold):**
- **Validates:** Handling of `atThreshold` flag for low-stock alerts
- **Verifies:** Correct interpretation of boundary conditions
- **Pitfall Check:** Prevents premature out-of-stock display

### Pitfalls & Mitigations

| Pitfall | Impact | Mitigation in Code |
|---------|--------|-------------------|
| **Schema Drift** | Wrong parameters sent, parsing errors | Strict validation in `adapter._validate_v2_params()`, Pydantic models recommended |
| **Missing regionId** | 400 error from v2 API | Pre-flight check in adapter, fallback to v1 |
| **Inconsistent Timestamps** | Parsing failures | ISO 8601 format enforced in mock, datetime parsing in service |
| **Eventual Consistency** | Stale data | Async handling with `requiresPolling` flag, polling logic for production |
| **No Idempotency** | Duplicate checks | Request ID recommended (not implemented in POC) |
| **Circuit Breaker Stuck** | All requests fail | Auto-reset after 60s timeout in `CircuitBreaker` class |

### Production Rollout Strategy

**Phase 1: Canary (Week 1)**
- 5% traffic to v2
- Feature flag: `USE_V2_API=true`
- Metrics: error rate <0.5%, latency p95 <+20%
- Rollback: Automatic if error rate >1%

**Phase 2: Gradual (Weeks 2-3)**
- Increase: 5% → 25% → 50% → 75% → 100%
- 48-hour soak at each step
- A/B test availability accuracy
- Monitor fallback rate (target <5%)

**Phase 3: Full Migration (Week 4)**
- 100% v2 traffic
- 7-day monitoring period
- Disable v1 fallback
- Archive v1 code

**Observability Requirements:**
- Dashboard: v1/v2 split, latency percentiles, error rates
- Alerts: Error rate >1%, fallback >10%, circuit breaker open
- Logs: Trace IDs for cross-service debugging
- Metrics: Request duration, cache hit rate, retry count

### Known Limitations

1. **Mock Fidelity:**
   - Mocks simulate responses but lack production database complexity
   - No network latency/jitter simulation
   - Simplified error scenarios

2. **Async Handling:**
   - POC uses `requiresPolling` flag but doesn't implement actual polling
   - Production should use webhooks or event-driven architecture
   - No timeout for pending states (could wait indefinitely)

3. **Security:**
   - No authentication/authorization tested
   - No rate limiting
   - No input sanitization for SQL injection, etc.

4. **Scale:**
   - Only 6 test cases (production needs hundreds)
   - No load/stress testing
   - No concurrent request handling

5. **State Management:**
   - In-memory stock DB (resets on restart)
   - No cache invalidation strategy
   - No distributed locking for inventory updates

**Recommended Production Validation:**
- Shadow traffic testing (mirror production to v2 without impacting users)
- Chaos engineering (inject faults, kill services, partition networks)
- Load testing at 2x peak capacity
- Security audit (penetration testing, OWASP Top 10)
- Canary metrics: error rate, latency p95/p99, availability accuracy

---

## Quick Reference

### One-Command Execution
```powershell
.\run_all.sh
```

### Individual Project Testing
```powershell
# Project A (v1)
cd Project_A_PreChange
.\setup.sh
.\run_tests.sh

# Project B (v2)
cd Project_B_PostChange
.\setup.sh
.\run_tests.sh
```

### View Results
```powershell
# View comparison report
Get-Content compare_report.md

# View JSON results
Get-Content results\results_pre.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
Get-Content results\results_post.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
Get-Content results\aggregated_metrics.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

### Troubleshooting
```powershell
# Check logs
Get-Content Project_A_PreChange\logs\log_pre.txt
Get-Content Project_B_PostChange\logs\log_post.txt

# Test mock servers manually
Invoke-WebRequest http://localhost:5001/health
Invoke-WebRequest http://localhost:5002/health

# Manually run test
cd Project_A_PreChange
& .\venv\Scripts\Activate.ps1
python tests\test_pre_change.py
```

---

*This guide provides comprehensive implementation details for the API migration evaluation framework.*
