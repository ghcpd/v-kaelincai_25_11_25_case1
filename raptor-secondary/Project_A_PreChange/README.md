# Project A – Pre-Change (Legacy Integration)

This service calls the legacy `/api/v1/checkStock` endpoint without region awareness.

## Run tests

- **PowerShell (Windows)**: `./run_tests.ps1`
- **bash**: `./run_tests.sh`

Artifacts are written to `results/results_pre.json`, `results/metrics_pre.json`, and logs to `logs/log_pre.txt`.

## Mock server

`mocks/mock_server_v1.py` provides a Flask mock of `/api/v1/checkStock` on port **5001**.

## Service

`src/cart_service_v1.py` exposes `check_availability()` and an optional `/cart/availability` HTTP wrapper when executed directly.
