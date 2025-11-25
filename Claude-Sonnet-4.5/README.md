# API Change Evaluation Framework

## Overview

This framework evaluates AI models' ability to implement and validate API migration from a legacy stock checking endpoint to a new region-aware availability API.

### Migration Scenario

**Legacy API (v1):** `/api/v1/checkStock`
- Simple stock check with SKU only
- Returns: `{sku, available, stock}`

**New API (v2):** `/api/v2/stock/availability`
- Region-aware availability with warehouse groups
- Requires: `{sku, regionId, warehouseGroup}`
- Returns: `{sku, available, quantity, availabilityStatus, syncTimestamp, ...}`
- Supports asynchronous/pending availability states

## Project Structure

```
chatWorkSpace/
├── test_data.json              # Canonical test cases (6 scenarios)
├── README.md                   # This file
├── run_all.sh                  # Master execution script
├── results/                    # Aggregated results
│   ├── results_pre.json
│   ├── results_post.json
│   └── aggregated_metrics.json
├── compare_report.md           # Final comparison report
├── Project_A_PreChange/        # Legacy v1 integration
│   ├── src/
│   │   └── cart_service_v1.py
│   ├── mocks/
│   │   └── mock_api_v1.py
│   ├── data/
│   │   └── test_data.json (symlink/copy)
│   ├── tests/
│   │   └── test_pre_change.py
│   ├── logs/
│   │   └── log_pre.txt
│   ├── results/
│   │   └── results_pre.json
│   ├── requirements.txt
│   ├── setup.sh
│   └── run_tests.sh
└── Project_B_PostChange/       # New v2 integration
    ├── src/
    │   ├── cart_service_v2.py
    │   └── adapter.py
    ├── mocks/
    │   └── mock_api_v2.py
    ├── data/
    │   ├── test_data.json (symlink/copy)
    │   └── expected_postchange.json
    ├── tests/
    │   └── test_post_change.py
    ├── logs/
    │   └── log_post.txt
    ├── results/
    │   └── results_post.json
    ├── requirements.txt
    ├── setup.sh
    └── run_tests.sh
```

## Test Cases

The framework includes 6 comprehensive test cases:

1. **TC001 - Normal Case:** Confirmed availability with sufficient stock
2. **TC002 - Boundary Case:** Zero quantity (out of stock)
3. **TC003 - Asynchronous Case:** Pending status requiring polling
4. **TC004 - Invalid Input:** Missing required parameter (regionId)
5. **TC005 - Error Case:** Service timeout/500 error with fallback
6. **TC006 - Boundary Case:** Stock at reserve threshold

## Quick Start

### Prerequisites

- Python 3.8+
- PowerShell (Windows) or Bash (Linux/Mac)
- Virtual environment support

### One-Click Execution

Run the complete evaluation (both projects):

```powershell
.\run_all.sh
```

This script will:
1. Set up Project A (Pre-Change) environment
2. Run all tests against legacy v1 API
3. Collect metrics and logs
4. Set up Project B (Post-Change) environment
5. Run all tests against new v2 API
6. Generate comparison report
7. Output `compare_report.md` with findings

### Individual Project Execution

**Project A (Legacy v1):**
```powershell
cd Project_A_PreChange
.\setup.sh        # One-time setup
.\run_tests.sh    # Run tests
```

**Project B (New v2):**
```powershell
cd Project_B_PostChange
.\setup.sh        # One-time setup
.\run_tests.sh    # Run tests
```

## Expected Outputs

### Per-Test Outputs
- **HTTP Status:** 200 (success), 400 (validation error), 500 (server error)
- **Availability Decision:** `{available, quantity, note}`
- **Fallback Indicators:** Whether fallback logic was triggered
- **Latency Metrics:** Request duration in milliseconds

### Aggregated Results

**results_pre.json** and **results_post.json** contain:
- Per-case pass/fail status
- Response times (p50, p95, p99)
- Error counts and retry attempts
- Fallback frequency

**compare_report.md** includes:
- Correctness comparison (pass rates)
- Latency analysis (pre vs post)
- Error/retry rate comparison
- Fallback behavior analysis
- Rollout recommendations

## Key Features

### Project A (Pre-Change)
- Simple v1 API integration
- Basic error handling
- No region awareness
- Baseline performance metrics

### Project B (Post-Change)
- **Region-Aware API:** Supports regionId and warehouseGroup
- **Async Handling:** Manages pending availability with polling simulation
- **Adapter Pattern:** Backward compatibility with fallback to v1
- **Validation:** Strict parameter validation
- **Circuit Breaker:** Error threshold monitoring
- **Feature Flag:** Toggle between v1 and v2

## Evaluation Criteria

1. **Correctness:** API calls use correct parameters and handle responses properly
2. **Compatibility:** Graceful fallback when v2 unavailable
3. **Async Handling:** Proper management of pending states
4. **Performance:** Latency impact of migration
5. **Error Resilience:** Handling malformed inputs, timeouts, 5xx errors
6. **Test Coverage:** All scenarios pass with expected outcomes

## Known Limitations

1. **Mock Fidelity:** Mock servers simulate but don't replicate production complexity
2. **Network Conditions:** Local execution doesn't simulate real network latency/jitter
3. **Load Testing:** Framework focuses on functional correctness, not high-load scenarios
4. **State Management:** Simplified async polling vs production webhook/event systems
5. **Security:** No authentication/authorization testing included

## Recommended Production Rollout

### Phase 1: Canary Deployment (Week 1)
- Deploy v2 integration to 5% of traffic
- Enable feature flag `USE_V2_API=true` for canary group
- Monitor error rates, latency p95, fallback frequency
- Rollback if error rate > 0.5% or latency degrades > 20%

### Phase 2: Gradual Rollout (Weeks 2-3)
- Increase to 25%, then 50%, then 100%
- Monitor async handling metrics (polling frequency, sync delays)
- A/B test user-facing availability accuracy

### Phase 3: Full Migration (Week 4)
- Disable fallback to v1 after 7 days at 100%
- Remove v1 dependencies
- Update documentation and runbooks

### Observability Requirements
- Dashboard: v1 vs v2 call distribution
- Alerts: v2 error rate > 1%, fallback rate > 10%
- Logs: Trace ID for cross-service debugging
- Metrics: Request duration, cache hit rate, retry count

## Pitfalls and Mitigations

| Pitfall | Impact | Mitigation |
|---------|--------|------------|
| Schema drift | Wrong parameters sent | Strict validation + Pydantic models |
| Missing regionId | v2 API rejects request | Pre-flight validation + user prompts |
| Inconsistent timestamps | Parsing errors | ISO 8601 parser + timezone handling |
| Eventual consistency | Stale availability | Poll with exponential backoff |
| No idempotency | Duplicate checks | Request ID + caching |

## File Descriptions

- **test_data.json:** Input test cases with expected outputs
- **cart_service_v1.py:** Legacy service using v1 API
- **cart_service_v2.py:** Updated service using v2 API
- **adapter.py:** Compatibility layer with fallback logic
- **mock_api_v1.py / mock_api_v2.py:** Mock upstream APIs
- **test_pre_change.py / test_post_change.py:** Test harnesses
- **run_tests.sh:** Per-project test execution
- **run_all.sh:** Master orchestration script

## Support

For questions or issues:
1. Check logs in `Project_*/logs/`
2. Review results JSON files for detailed error messages
3. Consult `compare_report.md` for analysis

## License

This evaluation framework is provided as-is for educational and testing purposes.
