import requests
import subprocess
import time
import json
import os
from multiprocessing import Process

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from cart_service_v1 import CartServiceV1

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MOCK_PORT = 5101

def start_mock():
    return subprocess.Popen([sys.executable, os.path.join(BASE_DIR, 'mocks', 'mock_v1.py')])

def run_tests():
    with open(os.path.join(BASE_DIR, 'data', 'test_data.json')) as f:
        cases = json.load(f)
    # start mock
    proc = start_mock()
    time.sleep(0.5)
    svc = CartServiceV1(f'http://localhost:{MOCK_PORT}')
    results = []
    for c in cases:
        params = {'mode': c.get('mode')}
        url = f'http://localhost:{MOCK_PORT}/api/v1/checkStock'
        try:
            r = requests.get(url, params={'sku':c.get('sku')}, timeout=3)
        except Exception as e:
            http_status = 0
        else:
            http_status = r.status_code
        parsed, duration_ms = svc.check_stock(c.get('sku'))
        ok = (http_status == c['expected']['http_status'])
        # simple check for availability
        if 'available' in c['expected']:
            ok = ok and (parsed.get('available') == c['expected']['available'])
        results.append({"id":c['id'], "http_status":http_status, "parsed":parsed, "duration_ms":duration_ms, "pass":ok})
    proc.terminate()
    with open(os.path.join(BASE_DIR, 'results', 'results_pre.json'), 'w') as out:
        json.dump(results, out, indent=2)
    print(json.dumps(results, indent=2))

if __name__=='__main__':
    os.makedirs(os.path.join(BASE_DIR, 'results'), exist_ok=True)
    run_tests()
