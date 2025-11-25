# Project_B_PostChange — v2 Integration & Adapter

This project implements a new `CartServiceV2` which calls `/api/v2/stock/availability` and supports:

- Additional parameters: `regionId`, `warehouseGroup`.
- Asynchronous handling: polls when availabilityStatus is `pending` until `confirmed` or timeout.
- Fallback behavior to the legacy v1 endpoint when v2 returns errors or missing input.

Quick run (Linux/macOS):

```bash
cd Project_B_PostChange
./run_tests.sh
```

Windows (PowerShell):

```powershell
python tests/test_post_change.py
```

Outputs:
- results/results_post.json — test results
- logs/log_post.txt — console output
