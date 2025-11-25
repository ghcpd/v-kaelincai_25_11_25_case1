import json
import os
import statistics
import sys
import time
from pathlib import Path

import requests
import socket
from rich.console import Console

# Ensure project root on sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parent  # repo root
for p in (BASE_DIR, ROOT_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from Project_A_PreChange.mocks import mock_server_v1  # type: ignore
from Project_B_PostChange.mocks import mock_server_v2  # type: ignore
from Project_B_PostChange.src.cart_service_v2 import check_availability_v2  # type: ignore

console = Console()
DATA_PATH = BASE_DIR / "data" / "test_data.json"
RESULTS_DIR = BASE_DIR / "results"
LOGS_DIR = BASE_DIR / "logs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_FILE = RESULTS_DIR / "results_post.json"
METRICS_FILE = RESULTS_DIR / "metrics_post.json"
LOG_FILE = LOGS_DIR / "log_post.txt"


def load_test_cases():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    # Start mocks (or reuse if already running)
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]

    v1_port = int(os.getenv("V1_PORT", find_free_port()))
    v2_port = int(os.getenv("V2_PORT", find_free_port()))

    def wait_for(url, max_wait_sec=5):
        start = time.time()
        while time.time() - start < max_wait_sec:
            try:
                resp = requests.post(url, json={"sku": "HEALTHCHECK"}, timeout=1)
                if resp.status_code in (200, 400, 500):
                    return True
            except Exception:
                time.sleep(0.3)
        return False

    v1_url = f"http://127.0.0.1:{v1_port}/api/v1/checkStock"
    v2_url = f"http://127.0.0.1:{v2_port}/api/v2/stock/availability"

    console.log(f"Ensuring V1 mock on {v1_port}")
    if not wait_for(v1_url, max_wait_sec=1):
        mock_server_v1.start_in_thread(port=v1_port)
        time.sleep(1.0)
        if not wait_for(v1_url, max_wait_sec=5):
            console.log(f"[yellow]Warning:[/yellow] V1 mock on {v1_port} did not respond to health check; proceeding anyway")

    console.log(f"Ensuring V2 mock on {v2_port}")
    if not wait_for(v2_url, max_wait_sec=1):
        mock_server_v2.start_in_thread(port=v2_port)
        time.sleep(1.0)
        if not wait_for(v2_url, max_wait_sec=5):
            console.log(f"[yellow]Warning:[/yellow] V2 mock on {v2_port} did not respond to health check; proceeding anyway")

    test_cases = load_test_cases()
    results = []
    latencies = []
    fallback_count = 0
    pass_count = 0

    for case in test_cases:
        case_id = case["id"]
        expected = case["expected_post"]
        reserve_threshold = case.get("reserveThreshold", 1)
        console.log(f"Running {case_id}: {case['description']}")

        start = time.perf_counter()
        result = check_availability_v2(
            sku=case["input"].get("sku"),
            region_id=case["input"].get("regionId"),
            warehouse_group=case["input"].get("warehouseGroup"),
            reserve_threshold=reserve_threshold,
            base_url=f"http://127.0.0.1:{v2_port}",
            fallback_url=f"http://127.0.0.1:{v1_port}",
        )
        duration_ms = (time.perf_counter() - start) * 1000
        result["latency_ms"] = result.get("latency_ms", duration_ms)
        latencies.append(result["latency_ms"])

        if result.get("fallback_used"):
            fallback_count += 1

        passed = (
            result.get("http_status") == expected.get("http_status")
            and result.get("availability", {}) == expected.get("availability", {})
            and bool(result.get("fallback_used")) == bool(expected.get("fallback_used"))
        )
        if passed:
            pass_count += 1

        results.append({
            "id": case_id,
            "description": case["description"],
            "input": case["input"],
            "expected": expected,
            "actual": result,
            "passed": passed,
        })

    metrics = {
        "total_cases": len(test_cases),
        "passed": pass_count,
        "pass_rate": pass_count / len(test_cases) if test_cases else 0,
        "latency_ms": {
            "p50": statistics.median(latencies) if latencies else None,
            "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 2 else None,
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
        "fallback_count": fallback_count,
        "fallback_rate": fallback_count / len(test_cases) if test_cases else 0,
        "error_rate": sum(1 for r in results if not r["passed"]) / len(results) if results else 0,
    }

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"results": results, "metrics": metrics}, f, indent=2)
    with open(METRICS_FILE, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(LOG_FILE, "w", encoding="utf-8") as logf:
        for r in results:
            logf.write(json.dumps(r) + "\n")

    console.log(f"Completed Project B tests. Passed {pass_count}/{len(test_cases)}")
    return pass_count == len(test_cases)


if __name__ == "__main__":
    success = main()
    raise SystemExit(0 if success else 1)
