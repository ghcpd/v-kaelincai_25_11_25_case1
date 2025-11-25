# Feature & Improvement – API Change Evaluation

## Scenario
Migrating inventory checks from legacy `/api/v1/checkStock` (no region awareness) to `/api/v2/stock/availability` (requires `regionId`, `warehouseGroup`, returns async fields like `availabilityStatus`, `syncTimestamp`).

### Expected Input / Output
- **v2 input** (JSON): `{ "sku": "ABC123", "regionId": "ap-sg-1", "warehouseGroup": "WG-2" }`
- **v2 response**: `{ "sku": "ABC123", "available": true, "quantity": 12, "availabilityStatus": "confirmed", "syncTimestamp": "2025-11-01T12:00:00Z" }`

### Acceptance Criteria
- Service calls v2 with required params.
- Handles `availabilityStatus: pending` via polling; falls back if exhausted.
- Graceful degradation/fallback to v1 on errors/invalids.
- Correct, or improved, user-facing availability vs baseline.

## Projects
- `Project_A_PreChange`: Legacy integration to v1.
- `Project_B_PostChange`: Updated integration with v2, polling, validation, and v1 fallback.

## Test Data
Canonical cases in `test_data.json` (root and per-project):
1. **TC1** Normal confirmed.
2. **TC2** Boundary (quantity == threshold).
3. **TC3** Async pending → confirmed (poll).
4. **TC4** Invalid input (missing regionId).
5. **TC5** High-latency/error (v2 timeout/500 → fallback).
6. **TC6** Malformed SKU (non-string).

Each case includes expected outputs for pre/post in `test_data.json` and `Project_B_PostChange/data/expected_postchange.json`.

## One-Click Execution
- **Windows PowerShell**: `./run_all.ps1`
- **bash**: `./run_all.sh`

Artifacts:
- `Project_A_PreChange/results/results_pre.json`
- `Project_B_PostChange/results/results_post.json`
- `results/aggregated_metrics.json`
- `compare_report.md`

## Environment & Mocks
- v1 mock: `http://127.0.0.1:5001` (`Project_A_PreChange/mocks/mock_server_v1.py`)
- v2 mock: `http://127.0.0.1:5002` (`Project_B_PostChange/mocks/mock_server_v2.py`)

Configurable via env:
- `V1_BASE_URL`, `V2_BASE_URL`, `V1_FALLBACK_URL`
- `ENABLE_V1_FALLBACK` (default `true`)
- `V2_POLL_INTERVAL_SEC` (default `0.5`), `V2_POLL_MAX_ATTEMPTS` (default `3`)

To toggle live vs mock, set the base URLs accordingly before running tests.

## Metrics Collected
- Pass/fail per case.
- Latency p50/p95/min/max.
- Fallback counts/rate (post-change).
- Error rates.

## Pitfalls & Mitigations
- **Schema drift**: Validate required params (`regionId`, `warehouseGroup`).
- **Async pending**: Poll with backoff and limit; fallback if exhausted.
- **Latency spikes**: Timeouts + fallback to v1; monitor p95.
- **Timestamp formats**: Use ISO8601 parsing; mock provides ISO strings.
- **Eventual consistency**: Idempotent polling; avoid duplicate decrements.
- **Resilience**: Circuit breakers, retries with jitter (add in prod).

## Limitations
- Mocks approximate behavior; real network conditions not simulated.
- Polling implemented with fixed intervals; no exponential backoff.
- No database/inventory reservation semantics modeled.

## Recommended Rollout
1. Ship v2 behind a feature flag.
2. Canary small traffic slice; compare `compare_report.md` metrics.
3. Monitor fallback/error rates; alert on regression.
4. Gradually ramp to 100%; keep v1 as emergency fallback.

## Structure
```
Project_A_PreChange/
Project_B_PostChange/
results/
run_all.ps1
run_all.sh
aggregate_results.py
```
