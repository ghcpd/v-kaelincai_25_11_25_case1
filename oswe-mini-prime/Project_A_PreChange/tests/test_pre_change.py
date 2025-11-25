import os
import time
import json
import requests
import subprocess
import signal
import shutil

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, 'data', 'test_data.json')

SERVICE_PORT = int(os.environ.get('SERVICE_PORT', 5000))
SERVICE_URL = f"http://localhost:{SERVICE_PORT}/check"

V1_PORT = int(os.environ.get('V1_PORT', 5001))
V1_BASE = f"http://localhost:{V1_PORT}"

LOG_FILE = os.path.join(ROOT, 'logs', 'log_pre.txt')
RESULTS_FILE = os.path.join(ROOT, 'results', 'results_pre.json')

# Helpers to start/stop subprocesses

def start_process(cmd, env=None, cwd=None, stdout=None, stderr=None):
    return subprocess.Popen(cmd, env=env, cwd=cwd, stdout=stdout, stderr=stderr)


def wait_for_url(url, timeout=10):
    start = time.time()
    while True:
        try:
            r = requests.get(url, timeout=0.5)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        if time.time() - start > timeout:
            raise RuntimeError(f'URL not available: {url}')
        time.sleep(0.1)


def run_tests():
    # load test data
    with open(DATA) as f:
        cases = json.load(f)

    # Start v1 mock server with configured behavior for cases
    # Start v1 with environment variables controlling latency and error
    env = os.environ.copy()

    # v1: configure delay for SLOW1 case to 10s; configure error for ABCERR
    # we use environment variable to set delay globally for test; alternatively we can mark in the mock via body
    env['V1_PORT'] = str(V1_PORT)
    env['V1_DELAY'] = '0'
    env['V1_ERROR_RATE'] = '0'

    v1_log = open(os.path.join(ROOT, 'logs', 'v1_mock.log'), 'wb')
    v1_proc = start_process(['python', 'mocks/v1_mock.py'], env=env, cwd=ROOT, stdout=v1_log, stderr=v1_log)

    # Start service
    service_env = os.environ.copy()
    service_env['SERVICE_PORT'] = str(SERVICE_PORT)
    service_env['V1_BASE'] = V1_BASE
    svc_log = open(os.path.join(ROOT, 'logs', 'cart_service_v1.log'), 'wb')
    service_proc = start_process(['python', 'src/cart_service_v1.py'], env=service_env, cwd=ROOT, stdout=svc_log, stderr=svc_log)

    # Wait for service and v1 to be ready
    wait_for_url(f"http://localhost:{V1_PORT}/")
    wait_for_url(f"http://localhost:{SERVICE_PORT}/")

    results = []

    for case in cases:
        testcase = case['id']
        header = f"Running {testcase}"
        print(header)
        if testcase == 'v1-error':
            # set error rate to 1 to trigger 500
            requests.post(f"{V1_BASE}/_admin/set_error_rate", json={'rate': 1.0})
            time.sleep(0.1)
        if testcase == 'high-latency':
            requests.post(f"{V1_BASE}/_admin/set_delay", json={'delay': 6.0})
            time.sleep(0.1)

        payload = {'sku': case['sku'], 'quantity': case['quantity']}
        start = time.time()
        try:
            r = requests.post(SERVICE_URL, json=payload, timeout=8)
            latency = time.time() - start
            result = {'id': testcase, 'status': r.status_code, 'latency': latency}
            if r.status_code == 200:
                result['body'] = r.json()
                # check expected
                exp = case.get('expected') or {}
                result['pass'] = True
                if exp.get('http_status') and exp.get('http_status') != r.status_code:
                    result['pass'] = False
                if exp.get('available') is not None and result['body'].get('available') != exp.get('available'):
                    result['pass'] = False
                if exp.get('quantity') is not None and result['body'].get('quantity') != exp.get('quantity'):
                    result['pass'] = False
            else:
                exp = case.get('expected') or {}
                result['pass'] = exp.get('http_status') == r.status_code
        except Exception as e:
            latency = time.time() - start
            result = {'id': testcase, 'status': 'error', 'error': str(e), 'latency': latency}
        finally:
            results.append(result)
            # reset v1 to defaults
            requests.post(f"{V1_BASE}/_admin/reset", json={})
            time.sleep(0.1)

    # persist results
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    # kill processes
    for p in (service_proc, v1_proc):
        p.terminate()
        try:
            p.wait(timeout=2)
        except Exception:
            p.kill()

    return results

if __name__ == '__main__':
    run_tests()
