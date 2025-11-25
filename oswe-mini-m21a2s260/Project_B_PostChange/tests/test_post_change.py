import requests
import subprocess
import time
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from cart_service_v2 import CartServiceV2

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MOCK_PORT = 5201

def start_mock():
    return subprocess.Popen([sys.executable, os.path.join(BASE_DIR, 'mocks', 'mock_v2.py')])

def run_tests():
    with open(os.path.join(BASE_DIR, 'data', 'test_data.json')) as f:
        cases = json.load(f)
    proc = start_mock()
    time.sleep(0.5)
    svc = CartServiceV2(f'http://localhost:{MOCK_PORT}')
    results = []
    for c in cases:
        # post uses service
        parsed, duration_ms = svc.check_stock(c.get('sku'))
        # expected safety checks
        ok = True
        if c['expected'].get('available') is not None:
            ok = ok and (parsed.get('available') == c['expected'].get('available'))
        results.append({"id":c['id'], "parsed":parsed, "duration_ms":duration_ms, "pass":ok})
    proc.terminate()
    with open(os.path.join(BASE_DIR, 'results', 'results_post.json'), 'w') as out:
        json.dump(results, out, indent=2)
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    os.makedirs(os.path.join(BASE_DIR, 'results'), exist_ok=True)
    run_tests()
