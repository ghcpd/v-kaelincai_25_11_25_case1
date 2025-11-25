import os
import time
import json
import requests
import subprocess

ROOT = os.path.dirname(os.path.dirname(__file__))
DATA = os.path.join(ROOT, 'data', 'test_data.json')

SERVICE_PORT = int(os.environ.get('SERVICE_PORT', 5000))
SERVICE_URL = f"http://localhost:{SERVICE_PORT}/check"

V1_PORT = int(os.environ.get('V1_PORT', 5001))
V1_BASE = f"http://localhost:{V1_PORT}"

V2_PORT = int(os.environ.get('V2_PORT', 6001))
V2_BASE = f"http://localhost:{V2_PORT}"

RESULTS_FILE = os.path.join(ROOT, 'results', 'results_post.json')


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
    with open(os.path.join(ROOT, '..', '..', 'test_data.json')) as f:
        cases = json.load(f)

    # Start v1 and v2 mock servers
    env = os.environ.copy()
    env['V1_PORT'] = str(V1_PORT)
    # normalize path to v1 mock (absolute path) to avoid incorrect relative resolution
    v1_root = os.path.abspath(os.path.join(ROOT, '..', 'Project_A_PreChange'))
    v1_log = open(os.path.join(v1_root, 'logs', 'v1_mock.log'), 'wb')
    v1_path = os.path.join(v1_root, 'mocks', 'v1_mock.py')
    v1_proc = start_process(['python', v1_path], env=env, cwd=v1_root, stdout=v1_log, stderr=v1_log)

    env2 = os.environ.copy()
    env2['V2_PORT'] = str(V2_PORT)
    v2_log = open(os.path.join(ROOT, 'logs', 'v2_mock.log'), 'wb')
    v2_proc = start_process(['python', 'mocks/v2_mock.py'], env=env2, cwd=ROOT, stdout=v2_log, stderr=v2_log)

    # Start service
    service_env = os.environ.copy()
    service_env['SERVICE_PORT'] = str(SERVICE_PORT)
    service_env['V1_BASE'] = V1_BASE
    service_env['V2_BASE'] = V2_BASE
    service_env['USE_V2'] = 'true'
    svc_log = open(os.path.join(ROOT, 'logs', 'cart_service_v2.log'), 'wb')
    service_proc = start_process(['python', 'src/cart_service_v2.py'], env=service_env, cwd=ROOT, stdout=svc_log, stderr=svc_log)

    time.sleep(1)
    wait_for_url(f"http://localhost:{V1_PORT}/")
    wait_for_url(f"http://localhost:{V2_PORT}/")
    wait_for_url(f"http://localhost:{SERVICE_PORT}/")

    results = []

    for case in cases:
        testcase = case['id']
        print('Running', testcase)
        # Set v2 behavior
        if testcase == 'async-pending':
            # set to pending initially and configure that a check later returns confirmed
            requests.post(f"{V2_BASE}/_admin/set_status", json={'sku': case['sku'], 'availabilityStatus': 'pending', 'available': False, 'quantity': 0})
            # schedule to flip to confirmed by posting after 0.8s
            def flip():
                time.sleep(0.8)
                requests.post(f"{V2_BASE}/_admin/set_status", json={'sku': case['sku'], 'availabilityStatus': 'confirmed', 'available': True, 'quantity': 10})
            import threading
            threading.Thread(target=flip).start()
        elif testcase == 'v2-error':
            # for v2-error SKU, the v2 mock returns 500 by design (sku endswith 'E')
            pass
        elif testcase == 'malformed-sku':
            pass
        else:
            # default: reset any previous state
            requests.post(f"{V2_BASE}/_admin/reset", json={})

        payload = { 'sku': case['sku'], 'quantity': case['quantity'], 'regionId': case.get('regionId'), 'warehouseGroup': case.get('warehouseGroup') }
        start = time.time()
        try:
            r = requests.post(SERVICE_URL, json=payload, timeout=10)
            latency = time.time() - start
            result = {'id': testcase, 'status': r.status_code, 'latency': latency}
            if r.status_code == 200:
                result['body'] = r.json()
                exp = case.get('expected_post', {})
                # basic checks
                result['pass'] = True
                if exp.get('http_status') and exp.get('http_status') != r.status_code:
                    result['pass'] = False
                if exp.get('available') is not None and result['body'].get('available') != exp.get('available'):
                    result['pass'] = False
                if exp.get('quantity') is not None and result['body'].get('quantity') != exp.get('quantity'):
                    result['pass'] = False
            else:
                exp = case.get('expected_post', {})
                result['pass'] = exp.get('http_status') == r.status_code
        except Exception as e:
            latency = time.time() - start
            result = {'id': testcase, 'status': 'error', 'error': str(e), 'latency': latency}

        results.append(result)

    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    for p in (service_proc, v2_proc, v1_proc):
        p.terminate()
        try:
            p.wait(timeout=2)
        except Exception:
            p.kill()

    return results

if __name__ == '__main__':
    run_tests()
