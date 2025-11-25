# API Migration Experiment: /api/v1/checkStock -> /api/v2/stock/availability

This repository contains two projects demonstrating a pre-change (legacy) integration and a post-change (v2) integration with robust tests and metrics.

Run the full workflow with: 

```
# On *nix
bash run_all.sh

# Or on Windows PowerShell (adapt if needed):
./run_all.sh
```

Results and a comparison report will be generated under `results/`.

See Project_A_PreChange/README.md and Project_B_PostChange/README.md for individual instructions.

## Acceptance Criteria
 - Pre-change implementation calls `/api/v1/checkStock` with `sku` and `quantity`.
 - Post-change implementation calls `/api/v2/stock/availability` with `sku`, `quantity`, `regionId`, and `warehouseGroup`.
 - Post-change handles `availabilityStatus: pending` by polling `/api/v2/stock/status` and falling back to v1 on timeout or failure.
 - Tests validate correct parsing, fallback counts, latency p50/p95, and pass/fail per case.

## Running
Run `bash run_all.sh` to execute tests for Project A and B then generate `compare_report.md`.

## Pitfalls & Limitations
- Mock servers cannot fully replicate production scale or eventual consistency across datacenters.
- Timeouts in test environment may not match production; adjust `POLL_TIMEOUT` and `POLL_INTERVAL` for realistic behavior.
- Feature flags should be added to production to do canary/ramping.

## Rollout Recommendations
- Use canary releases with 1% of traffic and gradually increase.
- Enable distributed tracing and correlation IDs across services.
- Add circuit-breakers & retries with jitter for v2.
- If v2 returns partial responses, add validation and use fallback adapter.

