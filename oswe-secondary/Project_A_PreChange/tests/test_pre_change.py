import json
import os
import subprocess
import time
import requests
from src.cart_service_v1 import CartServiceV1

MOCK_URL = os.environ.get('V1_MOCK', 'http://localhost:5001')


def start_mock():
    # start v1 mock if not already
    p = subprocess.Popen(['python', 'mocks/v1_mock.py'])
    time.sleep(0.6)
    return p


def stop_mock(p):
    p.terminate()
    p.wait(timeout=2)


def load_test_data():
    with open('data/test_data.json') as f:
        return json.load(f)


def run_cases():
    cases = load_test_data()
    svc = CartServiceV1(MOCK_URL)
    results = []
    for c in cases:
        expected = c['expected_pre']
        # configure mock according to case
        if 'mode' in c:
            requests.post(f'{MOCK_URL}/_admin/set_mode', json={'mode': c['mode'], 'delay': c.get('delay',0.0)})
        start = time.time()
        try:
            out = svc.check_stock(c['input'].get('sku'))
            status = 'ok'
            elapsed = time.time() - start
        except Exception as e:
            out = {'error': str(e)}
            status = 'error'
            elapsed = time.time() - start

        passed = (
            status == expected['status'] and
            (out.get('available') == expected.get('available'))
        )

        results.append({'case': c['name'], 'status': status, 'output': out, 'expected': expected, 'elapsed': elapsed, 'passed': passed})

    with open('results/results_pre.json', 'w') as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == '__main__':
    p = start_mock()
    try:
        res = run_cases()
        print('RESULTS', json.dumps(res, indent=2))
    finally:
        stop_mock(p)
