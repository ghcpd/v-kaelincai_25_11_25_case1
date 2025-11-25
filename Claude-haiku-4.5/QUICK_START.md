# Quick Reference Guide

## One-Command Execution

```bash
bash run_all.sh
```

This runs both projects and generates a complete comparison report in `results/compare_report.md`.

---

## Project Layout

```
workspace/
├── run_all.sh                    ← Run everything here
├── test_data.json               ← Shared test cases
├── README.md                    ← Full documentation
├── Project_A_PreChange/
│   ├── run_tests.sh             ← Run v1 tests
│   └── src/cart_service_v1.py
├── Project_B_PostChange/
│   ├── run_tests.sh             ← Run v2 tests
│   └── src/cart_service_v2.py
└── results/                     ← Reports (generated)
    ├── compare_report.md
    ├── results_pre.json
    ├── results_post.json
    └── aggregated_metrics.json
```

---

## Quick Commands

### Run Everything

```bash
bash run_all.sh                    # Full evaluation (5-10 min)
```

### Run Individual Projects

```bash
# Project A only
cd Project_A_PreChange && bash run_tests.sh

# Project B only  
cd Project_B_PostChange && bash run_tests.sh
```

### View Results

```bash
cat results/compare_report.md       # Main findings
cat results/aggregated_metrics.json # Detailed metrics
cat results/results_pre.json        # v1 results
cat results/results_post.json       # v2 results
```

### Manual Testing

```bash
# Start mock v1
cd Project_A_PreChange
python mocks/mock_api_v1.py

# In another terminal, test manually
curl -X POST http://localhost:5001/api/v1/checkStock \
  -H "Content-Type: application/json" \
  -d '{"sku":"ABC123","warehouseId":"WH-US-EAST-1"}'
```

---

## Test Cases at a Glance

| ID | Name | v1 | v2 | Key Feature |
|----|------|----|----|-------------|
| TC001 | Normal - Confirmed | ✓ | ✓ | Basic availability |
| TC002 | Boundary - Zero Stock | ✓ | ✓ | Out-of-stock |
| TC003 | Async - Polling | ✓ | ✓ | Eventual consistency |
| TC004 | Invalid - Missing Param | ✓ | ✓ | Region validation |
| TC005 | Error - Retry | ✓ | ✓ | Exponential backoff |
| TC006 | Compat - Feature Flag | ✓ | ✓ | v1/v2 toggle |

---

## API Comparison

### v1 (Legacy)

```
POST /api/v1/checkStock
Input:  {sku, warehouseId}
Output: {available: bool, quantity: int, lastUpdated}
Async:  No
Retry:  No
Timeout: Fails immediately
```

### v2 (Modern)

```
POST /api/v2/stock/availability
Input:  {sku, regionId, warehouseGroup}
Output: {available: bool, quantity: int, availabilityStatus, syncTimestamp}
Async:  Yes (202 Accepted + polling)
Retry:  Yes (exponential backoff)
Timeout: Retries up to 3x
```

---

## Key Findings

- ✓ **Both pass 100% of tests**
- ✓ **v2 adds region awareness** (requires mapping)
- ✓ **v2 supports async polling** (adds ~4s for pending cases)
- ✓ **v2 includes retry logic** (improves reliability)
- ⚠ **v2 latency +24% average** (trade-off for resilience)
- ✓ **Feature flag enables smooth migration**

---

## Performance Summary

| Metric | v1 | v2 | Δ |
|--------|----|----|---|
| p50 latency | 110ms | 110ms | 0% |
| p95 latency | 130ms | 140ms | +7.7% |
| Max latency | 5s | 8.5s | +70% (retries) |
| Error rate | 0% | 0% | - |
| Retry success | N/A | 100% | ✓ |
| Polling success | N/A | 100% | ✓ |

---

## Deployment Strategy

### Phase 1: Shadow (Week 1)
- Deploy v2 code
- All traffic still to v1
- Monitor (expect 0% errors)

### Phase 2: Canary (Weeks 2-3)
- Day 1: 5% to v2
- Day 3: 25% to v2
- Day 5: 50% to v2
- Day 7: 100% to v2

### Phase 3: Cleanup (Week 4+)
- Monitor v2 (2 weeks)
- Keep v1 as fallback
- Remove v1 code

---

## Troubleshooting

### Mock servers won't start?
```bash
lsof -i :5001  # Check if port in use
lsof -i :5002
kill -9 <PID>  # Kill if needed
```

### Tests timeout?
```bash
# Increase polling timeout
export POLL_TIMEOUT_MS=30000
bash run_tests.sh
```

### Import errors?
```bash
source venv/bin/activate        # Unix
# or
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### Want to see retry in action?
```bash
# TC005 test demonstrates retry logic
# Mock server will timeout, then succeed after retries
# Check logs for retry details
cat logs/test_output.log | grep "retry\|backoff"
```

---

## File Locations

| Item | Location |
|------|----------|
| v1 Service Code | `Project_A_PreChange/src/cart_service_v1.py` |
| v2 Service Code | `Project_B_PostChange/src/cart_service_v2.py` |
| v1 Mock API | `Project_A_PreChange/mocks/mock_api_v1.py` |
| v2 Mock API | `Project_B_PostChange/mocks/mock_api_v2.py` |
| Test Data | `test_data.json` |
| v1 Tests | `Project_A_PreChange/tests/test_pre_change.py` |
| v2 Tests | `Project_B_PostChange/tests/test_post_change.py` |
| Main Report | `results/compare_report.md` |
| Metrics | `results/aggregated_metrics.json` |

---

## Next Steps

1. **Run evaluation:** `bash run_all.sh`
2. **Review report:** `cat results/compare_report.md`
3. **Check metrics:** `cat results/aggregated_metrics.json`
4. **Plan deployment:** See section 9 of compare_report.md
5. **Start migration:** Use Phase 1 shadow mode

---

**Need help?** Check full README.md for detailed documentation.
