# Project B – Post-Change (v2 Integration & Adapter)

This service calls `/api/v2/stock/availability` with region+warehouse awareness, async handling, and optional fallback to v1.

## Run tests

- **PowerShell (Windows)**: `./run_tests.ps1`
- **bash**: `./run_tests.sh`

Artifacts are written to `results/results_post.json`, `results/metrics_post.json`, and logs to `logs/log_post.txt`.

## Mocks

- `mocks/mock_server_v2.py` (port **5002**) simulates v2, including pending → confirmed and error cases.
- Uses v1 mock from Project A on port **5001** for fallback.

## Service

`src/cart_service_v2.py` exposes `check_availability_v2()` and an optional `/cart/availability` HTTP wrapper when executed directly.

Supports env vars: `V2_BASE_URL`, `V1_FALLBACK_URL`, `V2_TIMEOUT`, `V2_POLL_INTERVAL_SEC`, `V2_POLL_MAX_ATTEMPTS`, `ENABLE_V1_FALLBACK`.
