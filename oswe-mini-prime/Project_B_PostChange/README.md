# Project_B_PostChange

This project implements the post-change cart service that calls `/api/v2/stock/availability` and includes an adapter and polling for async responses.

How to run tests (Unix):
```
cd Project_B_PostChange
bash setup.sh
bash run_tests.sh
```

Outputs:
- `results/results_post.json` - per-case responses and latencies
- `logs/` - service and test logs

Notes:
- The service supports `USE_V2` env var to toggle v2 usage.
- For pending responses, the service polls `/api/v2/stock/status` for up to `POLL_TIMEOUT` seconds.
- If v2 fails or times out, the service falls back to v1 for backward compatibility.
