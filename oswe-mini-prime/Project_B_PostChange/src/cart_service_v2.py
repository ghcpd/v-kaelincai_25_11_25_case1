from flask import Flask, request, jsonify
import requests
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cart_service_v2")

app = Flask(__name__)
import os as _os
logger.info(f"cart_service_v2 starting from {__file__}, mtime={_os.path.getmtime(__file__)}")

V1_BASE = os.environ.get('V1_BASE', 'http://localhost:5001')
V2_BASE = os.environ.get('V2_BASE', 'http://localhost:6001')
POLL_TIMEOUT = float(os.environ.get('POLL_TIMEOUT', '2.0'))
POLL_INTERVAL = float(os.environ.get('POLL_INTERVAL', '0.5'))
USE_V2 = os.environ.get('USE_V2', 'true').lower() == 'true'

@app.route('/check', methods=['POST'])
def check_stock():
    payload = request.json
    sku = payload.get('sku')
    quantity = payload.get('quantity', 1)
    region_id = payload.get('regionId')
    warehouse_group = payload.get('warehouseGroup')
    start = time.time()
    # If USE_V2 is disabled, call v1
    if not USE_V2:
        return _call_v1(sku, quantity)

    # Input validation: ensure SKU is a string
    if not isinstance(sku, str):
        logger.info(f"Received check request sku={sku} type={type(sku)} quantity={quantity}")
        return jsonify({'error': 'invalid sku'}), 400
    logger.info(f"Received check request sku={sku} type={type(sku)} quantity={quantity}")

    try:
        v2_payload = {'sku': sku, 'quantity': quantity, 'regionId': region_id, 'warehouseGroup': warehouse_group}
        resp = requests.post(f"{V2_BASE}/api/v2/stock/availability", json=v2_payload, timeout=5)
        if resp.status_code == 200:
            body = resp.json()
            status = body.get('availabilityStatus')
            if status == 'confirmed':
                return jsonify({'sku': sku, 'available': body.get('available', False), 'quantity': body.get('quantity', 0), 'note':'v2_confirmed'}), 200
            elif status == 'pending':
                # Poll until timeout
                sync_ts = body.get('syncTimestamp')
                # Polling loop
                deadline = time.time() + POLL_TIMEOUT
                while time.time() < deadline:
                    time.sleep(POLL_INTERVAL)
                    resp2 = requests.post(f"{V2_BASE}/api/v2/stock/status", json={'sku': sku}, timeout=2)
                    if resp2.status_code == 200:
                        b2 = resp2.json()
                        if b2.get('availabilityStatus') == 'confirmed':
                            return jsonify({'sku': sku, 'available': b2.get('available', False), 'quantity': b2.get('quantity', 0), 'note':'v2_confirmed_after_poll'}), 200
                # Poll timed out -- fall back to v1
                logger.info('v2 pending timed out; falling back to v1')
                return _call_v1(sku, quantity)
            else:
                # Partial or unknown -> fallback
                return _call_v1(sku, quantity)
        else:
            logger.warning('v2 returned non-200; fallback')
            return _call_v1(sku, quantity)
    except requests.exceptions.RequestException as e:
        logger.exception('v2 request failed')
        return _call_v1(sku, quantity)


def _call_v1(sku, quantity):
    try:
        r = requests.post(f"{V1_BASE}/api/v1/checkStock", json={'sku':sku, 'quantity': quantity}, timeout=5)
        if r.status_code == 200:
            body = r.json()
            return jsonify({'sku':body.get('sku'), 'available': body.get('available', False), 'quantity': body.get('quantity', 0), 'note': 'v1_adapter'}), 200
        elif r.status_code == 400:
            try:
                return jsonify(r.json()), 400
            except Exception:
                return jsonify({'error': 'upstream bad request'}), 400
        else:
            return jsonify({'error':'upstream v1 error'}), 502
    except requests.exceptions.RequestException:
        return jsonify({'error':'timeout'}), 504


@app.route('/', methods=['GET'])
def root():
    return 'cart service v2 ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('SERVICE_PORT', 5000))
    app.run(host='0.0.0.0', port=port)
