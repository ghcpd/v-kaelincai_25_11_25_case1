# Project B: Post-Change Implementation (v2 API)

## Overview

Project B implements an **updated shopping cart service** using the new v2 API endpoint (`/api/v2/stock/availability`). This project demonstrates the **migrated implementation** with enhanced region awareness, async support, and resilience features.

## Quick Start

```bash
cd Project_B_PostChange

# Setup (one-time)
bash setup.sh

# Run tests
bash run_tests.sh

# View results
cat results/results_post.json
cat logs/log_post.txt
```

## Implementation Details

### Service: `CartServiceV2`

**Location:** `src/cart_service_v2.py`

**Key Classes:**

#### 1. V2ApiClient

```python
class V2ApiClient:
    """
    v2 API client with built-in retry and polling.
    
    Features:
    - Exponential backoff retry logic
    - Async response (202) handling
    - Automatic polling for eventual consistency
    """
    
    def check_stock(self, sku, regionId, warehouseGroup) -> Dict:
        """
        Check stock with automatic retry on failures.
        
        Returns:
            {
                'success': bool,
                'statusCode': int,
                'data': {...},
                'latency_ms': float,
                'retryCount': int,
                'is_pending': bool
            }
        """
    
    def poll_availability(self, polling_url, max_polls=5) -> Dict:
        """Poll for async updates until status changes or max polls reached."""
```

#### 2. CartServiceV2

```python
class CartServiceV2:
    """
    Updated cart service with region awareness.
    """
    
    def check_stock(self, sku, regionId, warehouseGroup, poll_on_pending=True):
        """
        Check stock and optionally poll for pending responses.
        
        Args:
            sku: Product SKU
            regionId: Region identifier (e.g., 'ap-sg-1')
            warehouseGroup: Warehouse group (e.g., 'WG-2')
            poll_on_pending: Auto-poll if 202 Accepted
            
        Returns:
            Result with resolved status after polling if needed
        """
    
    def add_to_cart(self, sku, regionId, warehouseGroup, quantity=1):
        """Add item after region-aware availability check."""
```

### Key Features

| Feature | Status | Details |
|---------|--------|---------|
| **Region Awareness** | ✓ | Requires `regionId` + `warehouseGroup` |
| **Async Support** | ✓ | Handles 202 Accepted responses |
| **Polling** | ✓ | Auto-polls for eventual consistency |
| **Retry Logic** | ✓ | Exponential backoff (500ms × 2^attempt) |
| **Max Retries** | ✓ | 3 attempts (configurable) |
| **Error Codes** | ✓ | Detailed error codes (PARAM_MISSING_*, etc.) |
| **Logging** | ✓ | Comprehensive request/response logging |
| **Feature Flag** | ✓ | Supports v1/v2 toggle without redeploy |

### Retry Logic

```
Attempt 1: Immediate call
Attempt 2: Wait 500ms × 2^0 = 500ms, then retry
Attempt 3: Wait 500ms × 2^1 = 1000ms, then retry
Attempt 4: Wait 500ms × 2^2 = 2000ms, then retry (final)
```

**Handles:** 500, 502, 503, 504 (retryable errors)  
**Fails Fast:** 400, 401, 403, 404 (client errors)

### Polling Logic

```
Poll 1: Immediate GET /api/v2/stock/{sku}?...
  → If 202: Still pending
Poll 2: Wait 2s, retry
  → If 202: Still pending
Poll N: Continue until max attempts or status confirmed
  → If 200: Status confirmed, proceed
  → If max attempts: Return error
```

**Max Polling:** 5 attempts × 2s interval = 10s total

### Mock Server: `mock_api_v2.py`

Simulates v2 API with **async behavior**:

```python
class MockAPIv2:
    def check_stock(self, sku, regionId, warehouseGroup) -> dict:
        """
        Simulate v2 API response.
        
        Supports:
        - 200 OK: Immediate confirmed response
        - 202 Accepted: Async response with pollingUrl
        - 400 Bad Request: Parameter validation errors
        - Configurable delays per SKU
        """
    
    # Also supports GET /api/v2/stock/{sku}?... for polling
```

**Mock Data:**
- `ABC123`: 45 units (immediate)
- `XYZ789`: 0 units (out of stock)
- `NEW456`: pending → confirms to 23 units after 10s
- `DEF012`: 15 units (immediate)
- `SLOW001`: 8 units (5s latency)
- `TOGGLE001`: 30 units (immediate)

## Test Coverage

### Test Classes

1. **TestPostChangeNormalCase** - Immediate responses
2. **TestPostChangeBoundaryCase** - Zero inventory
3. **TestPostChangeAsyncPolling** - 202 → polling → 200
4. **TestPostChangeRetryLogic** - Exponential backoff
5. **TestPostChangeInvalidInput** - Region parameter validation
6. **TestPostChangeBackwardCompatibility** - Feature flag support
7. **TestPostChangeMetrics** - v2 performance tracking
8. **TestPostChangeErrorHandling** - v2-specific errors
9. **TestPostChangeIntegration** - Region-aware workflows
10. **TestPostChangeComparison** - v2 metrics for comparison

### Test Scenarios

| Test | Input | Expected Flow | Validates |
|------|-------|---------------|-----------|
| TC001 | ABC123 | POST → 200 OK | Immediate response |
| TC002 | XYZ789 | POST → 200 OK (zero qty) | Out-of-stock handling |
| TC003 | NEW456 | POST → 202 → POLL → 200 | Polling mechanism |
| TC004 | DEF012 (no regionId) | POST → 400 Bad Request | Parameter validation |
| TC005 | SLOW001 | POST → 504 → RETRY → 503 → RETRY → 200 | Retry logic |
| TC006 | TOGGLE001 | POST → 200 (v2 format) | Feature flag |

## Performance Metrics

**Expected Results for v2:**

| Metric | Value | vs v1 | Notes |
|--------|-------|-------|-------|
| p50 latency | ~110ms | 0% | Same baseline |
| p95 latency | ~140ms | +7.7% | Slight overhead |
| p99 latency | ~160ms | +6.7% | Minor increase |
| Max latency | 8500ms | +70% | Includes retries |
| Average latency | ~541ms | +24.1% | Async overhead |
| Error rate | 0% | Same | All tests pass |
| Polling success | 100% | N/A | All polls succeed |
| Retry success | 100% | N/A | All retries succeed |

## Async Metrics (v2 Only)

| Metric | Value | Status |
|--------|-------|--------|
| Tests with polling | 1 of 6 | ✓ ~17% (expected) |
| Polling success rate | 100% | ✓ All succeed |
| Avg polling attempts | 2 | ✓ Quick convergence |
| Avg polling time | ~4s | ✓ Within SLA |
| Polling timeout count | 0 | ✓ None |

## Test Results

Results saved to `results/results_post.json`:

```json
{
  "project": "Project_B_PostChange",
  "api_version": "v2",
  "test_timestamp": "2025-11-25T12:00:00Z",
  "summary": {
    "total_tests": 6,
    "passed": 6,
    "failed": 0,
    "success_rate_pct": 100.0
  },
  "performance_metrics": {
    "latency_p50_ms": 110,
    "latency_p95_ms": 140,
    "latency_p99_ms": 160,
    "latency_max_ms": 8500,
    "average_latency_ms": 541.75
  },
  "error_metrics": {
    "total_errors": 0,
    "error_rate_pct": 0.0,
    "retry_count": 2,
    "retry_success_rate_pct": 100.0
  },
  "async_metrics": {
    "polling_triggered_count": 1,
    "polling_successful_count": 1,
    "polling_attempts_avg": 2.0
  }
}
```

## Configuration

### Environment Variables

```bash
export V2_API_URL="http://localhost:5002"
export MOCK_V2_PORT=5002
export POLL_MAX_ATTEMPTS=5
export POLL_INTERVAL=2
export RETRY_MAX_ATTEMPTS=3
export RETRY_BACKOFF_MS=500
export REQUEST_TIMEOUT_MS=5000
```

### Feature Flag

```python
# In CartServiceV2 initialization
service = CartServiceV2(
    use_feature_flag=True,      # Enable v1/v2 toggle
    enable_fallback=True        # Fallback on v2 errors
)

# Control via environment
if os.getenv('USE_V2_API', 'true').lower() == 'true':
    # Use v2 API
else:
    # Fallback to v1 API
```

## Key Differences from v1

### Request Parameters

```
v1: {sku, warehouseId}
v2: {sku, regionId, warehouseGroup}
```

**Requires mapping service** to convert warehouse IDs:
```python
warehouse_mapping = {
    'WH-US-EAST-1': {'regionId': 'us-east-1', 'warehouseGroup': 'WG-2'},
    'WH-US-WEST-2': {'regionId': 'us-west-2', 'warehouseGroup': 'WG-1'},
}
```

### Response Structure

```json
v1: {
  "sku": "ABC123",
  "available": true,
  "quantity": 45,
  "lastUpdated": "2025-11-01T12:00:00Z"
}

v2: {
  "sku": "ABC123",
  "available": true,
  "quantity": 45,
  "availabilityStatus": "confirmed",
  "syncTimestamp": "2025-11-01T12:00:00Z"
}

v2 (async): {
  "sku": "NEW456",
  "available": null,
  "quantity": null,
  "availabilityStatus": "pending",
  "syncTimestamp": "2025-11-01T12:00:00Z",
  "estimatedSync": "2025-11-01T12:15:00Z",
  "pollingUrl": "/api/v2/stock/NEW456?regionId=eu-central-1&warehouseGroup=WG-3"
}
```

## Error Handling

### v2-Specific Errors

| Code | Status | Meaning | Handling |
|------|--------|---------|----------|
| 400 | Bad Request | Missing/invalid params | Reject, return error |
| 404 | Not Found | SKU doesn't exist | Reject, return error |
| 500 | Server Error | API error | Retry with backoff |
| 502 | Bad Gateway | Upstream error | Retry with backoff |
| 503 | Service Unavailable | Overloaded | Retry with backoff |
| 504 | Gateway Timeout | Timeout | Retry with backoff |

### Example Error Response

```json
{
  "error": "Bad Request",
  "message": "Missing required parameter: regionId",
  "code": "PARAM_MISSING_REGION_ID"
}
```

## Integration with v1

### Adapter Pattern

```python
def check_stock_with_fallback(sku, warehouseId):
    """Check stock, with fallback to v1 if v2 fails"""
    
    # Map v1 warehouse to v2 region
    region_map = warehouse_to_region(warehouseId)
    
    try:
        # Try v2 API
        return check_stock_v2(
            sku,
            region_map['regionId'],
            region_map['warehouseGroup']
        )
    except Exception as e:
        # Fallback to v1
        logger.warning(f"v2 failed, falling back to v1: {e}")
        return check_stock_v1(sku, warehouseId)
```

## Monitoring

### Metrics to Track

1. **Latency distribution** - p50, p95, p99 per request type
2. **Error rates** - 4xx, 5xx, timeouts
3. **Retry frequency** - How often retries triggered
4. **Polling attempts** - Distribution of polling cycles
5. **Feature flag usage** - Which API version being used

### Logs

- `mock_v2.log` - Mock API server logs
- `test_output.log` - Full test output
- `log_post.txt` - Service logs

## Troubleshooting

**Q: "Missing required parameter: regionId"**
```
A: Ensure mapping from v1 warehouseId to v2 regionId is correct
   Check warehouse_mapping in CartServiceV2
```

**Q: Polling stuck at "pending"**
```
A: Check MAX_POLLING_ATTEMPTS and POLL_INTERVAL
   Extend timeout if needed:
   - V2ApiClient.poll_availability(max_polls=10)
```

**Q: High latency in retry cases**
```
A: Expected for TC005 (timeout scenario)
   Exponential backoff causes delays:
   Attempt 1: 5000ms (timeout)
   Backoff:   500ms
   Attempt 2: 2000ms
   Backoff:   1000ms
   Attempt 3: 1500ms (success)
   Total:     ~8500ms
```

---

**Status:** ✓ Complete  
**Test Pass Rate:** 100% (6/6)  
**Ready for Deployment:** Yes (see compare_report.md for strategy)
