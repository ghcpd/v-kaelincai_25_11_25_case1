import subprocess
import time
import sys
import os
# ensure src on path before importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import json
import os
import signal
import requests
from cart_service_v1 import CartServiceV1

# removed duplicate import; using direct module import by path entry

BASE = os.path.dirname(__file__)

def start_mock():
    path = os.path.join(BASE, '..', 'mocks', 'mock_v1.py')
    proc = subprocess.Popen([sys.executable, path])
    time.sleep(0.4)
    return proc

def stop_mock(proc):
    proc.terminate()

def test_prechange_cases():
    proc = start_mock()
    try:
        svc = CartServiceV1('http://localhost:5101')
        with open(os.path.join(BASE, '..', 'data', 'test_data.json')) as f:
            cases = json.load(f)
        for c in cases:
            parsed, dur = svc.check_stock(c.get('sku'))
            assert parsed is not None
            # Check expected availability if present
            if 'available' in c['expected']:
                assert parsed.get('available') == c['expected']['available']
    finally:
        stop_mock(proc)
