# API Migration Demo: Pre vs Post Change

Run the comparison using `run_all.sh` in a Windows PowerShell shell. Each project has its own `run_tests.sh` and `setup.sh` to create a venv and install dependencies. The top-level `run_all.sh` runs both projects, aggregates results to `results/`, and writes `compare_report.md`.

Project A (legacy) calls `/api/v1/checkStock`.
Project B (post-change) calls `/api/v2/stock/availability` with regionId and warehouseGroup, supports pending status with polling.

See `compare_report.md` after running `run_all.sh`.

Acceptance criteria:
- Pre-change uses `/api/v1/checkStock` with legacy parameters and schema.
- Post-change uses `/api/v2/stock/availability` with regionId and warehouseGroup, handles `availabilityStatus` pending via polling, and falls back on errors.

Limitations: this is a local mock-based test and may not reflect production network variability. Use canary rollout in production as recommended.
