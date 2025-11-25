# Project A: Pre-Change Implementation (v1 API)

## Overview

Project A implements a shopping cart service using the **legacy v1 API** endpoint (`/api/v1/checkStock`). This project serves as the **baseline** for the migration evaluation.

## Quick Start

```bash
cd Project_A_PreChange

# Setup (one-time)
bash setup.sh

# Run tests
bash run_tests.sh

# View results
cat results/results_pre.json
cat logs/log_pre.txt
```

## Implementation Details

### Service: `CartServiceV1`

**Location:** `src/cart_service_v1.py`

**Key Methods:**

```python
def check_stock(self, sku: str, warehouseId: str) -> Dict[str, Any]:
    """
    Check inventory availability using v1 API.
    
    Args:
        sku: Product SKU
        warehouseId: Warehouse identifier
        
    Returns:
        {
            'success': bool,
            'statusCode': int,
            'data': {
                'sku': str,
                'available': bool,
                'quantity': int,
                'lastUpdated': str (ISO8601)
            },
            'latency_ms': float,
            'error': str or None
        }
    """
```

```python
def add_to_cart(self, sku: str, warehouseId: str, quantity: int = 1) -> Dict[str, Any]:
    """
    Add item to cart after checking availability.
    
    Returns:
        {
            'added': bool,
            'reason': str,
            'quantity_added': int,
            'latency_ms': float
        }
    """
```

### Characteristics

| Aspect | Details |
|--------|---------|
| **Endpoint** | `POST /api/v1/checkStock` |
| **Parameters** | `sku`, `warehouseId` (2 required) |
| **Response Format** | `{available: bool, quantity: int, lastUpdated}` |
| **Async Support** | ✗ No (synchronous only) |
| **Retry Logic** | ✗ No (direct call) |
| **Region Awareness** | ✗ No |
| **Error Handling** | Basic (HTTP status codes) |
| **Timeout Behavior** | Fails immediately at 5s timeout |

### Mock Server: `mock_api_v1.py`

Simulates the v1 API with configurable behavior:

```python
class MockAPIv1:
    def check_stock(self, sku: str, warehouseId: str) -> dict:
        """
        Simulate v1 API response.
        
        Supports:
        - Normal responses (200 OK)
        - Delayed responses (configurable latency)
        - Not found (404)
        - Null values for in-progress updates
        """
```

**Mock Data:**
- `ABC123`: 45 units available
- `XYZ789`: 0 units (out of stock)
- `NEW456`: null quantity (update in progress)
- `DEF012`: 15 units available
- `SLOW001`: 8 units (5s latency)
- `TOGGLE001`: 30 units available

## Test Coverage

### Test Classes

1. **TestPreChangeNormalCase** - Basic functionality
2. **TestPreChangeBoundaryCase** - Edge cases (zero inventory)
3. **TestPreChangeAsyncCase** - Handling of null/pending states
4. **TestPreChangeInvalidInput** - Parameter validation
5. **TestPreChangeErrorHandling** - Timeout and error scenarios
6. **TestPreChangeMetrics** - Performance metric collection
7. **TestPreChangeIntegration** - End-to-end workflows
8. **TestPreChangeComparison** - Baseline metrics for v1 vs v2 comparison

### Test Data

All tests reference `test_data.json`:

```json
{
  "config": {
    "v1_base_url": "http://localhost:5001",
    "v1_endpoint": "/api/v1/checkStock",
    "timeout_ms": 5000
  },
  "test_cases": [
    {
      "id": "TC001",
      "category": "normal",
      "v1_request": {"sku": "ABC123", "warehouseId": "WH-US-EAST-1"},
      "v1_expected_response": {
        "statusCode": 200,
        "body": {"sku": "ABC123", "available": true, "quantity": 45}
      }
    },
    // ... more test cases
  ]
}
```

## Performance Baseline

**Expected Results for v1:**

| Metric | Value | Notes |
|--------|-------|-------|
| p50 latency | ~110ms | Typical response |
| p95 latency | ~130ms | Slightly slower requests |
| p99 latency | ~150ms | Edge cases |
| Max latency | 5000ms | Timeout scenario (SLOW001) |
| Average latency | ~436ms | Weighted by test distribution |
| Error rate | 0% | All tests pass |
| Success rate | 100% | All requests successful |

## Test Results

Results are saved to `results/results_pre.json`:

```json
{
  "project": "Project_A_PreChange",
  "api_version": "v1",
  "test_timestamp": "2025-11-25T12:00:00Z",
  "summary": {
    "total_tests": 6,
    "passed": 6,
    "failed": 0,
    "success_rate_pct": 100.0
  },
  "performance_metrics": {
    "latency_p50_ms": 110,
    "latency_p95_ms": 130,
    "latency_p99_ms": 150,
    "latency_max_ms": 5000,
    "average_latency_ms": 436.75
  },
  "error_metrics": {
    "total_errors": 0,
    "error_rate_pct": 0.0,
    "timeout_count": 0,
    "retry_count": 0
  }
}
```

## Logs

Test execution logs are saved to `logs/`:

- `mock_v1.log` - Mock API server logs
- `test_output.log` - Full test suite output
- `log_pre.txt` - Service logs during test

## Limitations

1. **No Async Support** - Cannot handle eventual consistency
2. **No Retry Logic** - Fails on transient errors
3. **Single Warehouse** - No region-aware inventory
4. **Limited Error Info** - Only HTTP status codes
5. **No Polling** - Cannot wait for inventory updates

## Next Steps

After reviewing v1 baseline:
1. Compare with Project B (v2) results
2. Analyze performance differences
3. Review `compare_report.md` for detailed findings
4. Plan v2 migration strategy

## Troubleshooting

**Q: Mock server won't start**
```bash
# Check port 5001 is available
lsof -i :5001
# Kill if needed
kill -9 <PID>
```

**Q: Timeout on SLOW001 test**
```bash
# Expected! TC005 tests timeout handling
# Mock server deliberately delays response
```

**Q: Import errors**
```bash
# Ensure venv activated
source venv/bin/activate
# Reinstall deps
pip install -r requirements.txt
```

---

**Status:** ✓ Complete  
**Test Pass Rate:** 100% (6/6)  
**Ready for Comparison:** Yes
