import subprocess

import time
import sys
import os
# ensure src on path before importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import json
import os
import signal
import sys

from cart_service_v2 import CartServiceV2

BASE = os.path.dirname(__file__)

def start_mock():
    path = os.path.join(BASE, '..', 'mocks', 'mock_v2.py')
    proc = subprocess.Popen([sys.executable, path])
    time.sleep(0.4)
    return proc

def stop_mock(proc):
    proc.terminate()

def test_postchange_cases():
    proc = start_mock()
    try:
        svc = CartServiceV2('http://localhost:5201')
        with open(os.path.join(BASE, '..', 'data', 'test_data.json')) as f:
            cases = json.load(f)
        for c in cases:
            parsed, dur = svc.check_stock(c.get('sku'))
            assert parsed is not None
            if 'expected' in c and 'available' in c['expected']:
                assert parsed.get('available') == c['expected']['available']
    finally:
        stop_mock(proc)
