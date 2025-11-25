# Project_A_PreChange

This project implements the legacy cart service that calls `/api/v1/checkStock`.

How to run tests:

Windows (PowerShell):
```
cd Project_A_PreChange
.\setup.sh # or use run in Git Bash
.\run_tests.sh
```

Unix:
```
cd Project_A_PreChange
bash setup.sh
bash run_tests.sh
```

Outputs:
- `results/results_pre.json` - per-case responses and latencies
- `logs/` - service and test logs

The pre-change service does not include region-awareness and simply maps the v1 schema.
