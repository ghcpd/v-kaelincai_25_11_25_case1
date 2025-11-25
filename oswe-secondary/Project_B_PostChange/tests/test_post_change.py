import json
import os
import subprocess
import time
import requests
from src.cart_service_v2 import CartServiceV2

V2_MOCK = os.environ.get('V2_MOCK', 'http://localhost:6001')
V1_MOCK = os.environ.get('V1_MOCK', 'http://localhost:5001')


def start_mocks():
    # start the v1 mock located in sibling Project_A_PreChange
    v1_path = os.path.abspath(os.path.join(os.getcwd(), '..', 'Project_A_PreChange', 'mocks', 'v1_mock.py'))
    v2_path = os.path.abspath(os.path.join(os.getcwd(), 'mocks', 'v2_mock.py'))
    p1 = subprocess.Popen(['python', v1_path])
    p2 = subprocess.Popen(['python', v2_path])
    time.sleep(0.6)
    return p1, p2


def stop_mocks(ps):
    for p in ps:
        try:
            p.terminate()
            p.wait(timeout=2)
        except Exception:
            pass


def load_test_data():
    with open('../test_data.json') as f:
        return json.load(f)


def configure_case(case):
    # configure v1 mode
    if 'mode_v1' in case:
        requests.post(f'{V1_MOCK}/_admin/set_mode', json={'mode': case['mode_v1'], 'delay': case.get('delay',0.0)})
    # configure v2 state
    if 'mode_v2' in case:
        # different v2 internal representations
        if case['mode_v2'] == 'confirmed':
            requests.post(f'{V2_MOCK}/_admin/set_state', json={'sku': case['input']['sku'], 'mode': 'confirmed', 'syncTimestamp': '2025-11-01T12:00:00Z'})
        elif case['mode_v2'] == 'confirmed_zero':
            requests.post(f'{V2_MOCK}/_admin/set_state', json={'sku': case['input']['sku'], 'mode': 'confirmed_zero', 'syncTimestamp': '2025-11-01T12:00:00Z'})
        elif case['mode_v2'] == 'pending_then_confirm':
            requests.post(f'{V2_MOCK}/_admin/set_state', json={'sku': case['input']['sku'], 'mode': 'pending_then_confirm', 'syncTimestamp': '2025-11-01T12:00:00Z', 'calls': 0})
        elif case['mode_v2'] == 'bad_input':
            requests.post(f'{V2_MOCK}/_admin/set_state', json={'sku': case['input']['sku'], 'mode': 'bad_input'})
        elif case['mode_v2'] == 'error_or_slow':
            # instruct slow path
            requests.post(f'{V2_MOCK}/_admin/set_state', json={'sku': case['input']['sku'], 'mode': 'error_or_slow', 'cause': '500'})


def run_cases():
    cases = load_test_data()
    svc = CartServiceV2(V2_MOCK, V1_MOCK, timeout=1.0, poll_interval=0.2, poll_timeout=3.0)
    results = []
    for c in cases:
        configure_case(c)
        start = time.time()
        try:
            inp = c['input']
            out = svc.check_stock(inp.get('sku'), regionId=inp.get('regionId'), warehouseGroup=inp.get('warehouseGroup'))
            status = 'ok'
        except Exception as e:
            out = {'error': str(e)}
            status = 'error'
        elapsed = time.time() - start

        expected = c.get('expected_post')
        passed = False
        if expected['status'] == 'ok' and status == 'ok' and out.get('available') == expected.get('available'):
            passed = True
        elif expected['status'] == 'fallback' and (out.get('note', '').startswith('used_v1') or out.get('note', '') == 'v2_error_fallback'):
            passed = True

        results.append({'case': c['name'], 'status': status, 'output': out, 'expected': expected, 'elapsed': elapsed, 'passed': passed})

    with open('results/results_post.json', 'w') as f:
        json.dump(results, f, indent=2)

    return results


if __name__ == '__main__':
    os.makedirs('results', exist_ok=True)
    p1 = subprocess.Popen(['python', os.path.abspath(os.path.join(os.getcwd(), '..', 'Project_A_PreChange', 'mocks', 'v1_mock.py'))])
    p2 = subprocess.Popen(['python', os.path.abspath(os.path.join(os.getcwd(), 'mocks', 'v2_mock.py'))])
    try:
        time.sleep(0.5)
        res = run_cases()
        print('RESULTS', json.dumps(res, indent=2))
    finally:
        p1.terminate()
        p2.terminate()
