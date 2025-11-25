from flask import Flask, request, jsonify
import requests
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cart_service_v1")

app = Flask(__name__)
import os as _os
logger.info(f"cart_service_v1 starting from {__file__}, mtime={_os.path.getmtime(__file__)}")

V1_BASE = os.environ.get("V1_BASE", "http://localhost:5001")

@app.route('/check', methods=['POST'])
def check_stock():
    payload = request.json
    sku = payload.get('sku')
    quantity = payload.get('quantity', 1)
    logger.info(f"Received check request sku={sku} type={type(sku)} quantity={quantity}")
    print(f"[DEBUG] Received check request sku={sku} type={type(sku)} quantity={quantity}")
    # Input validation: ensure SKU is a string
    logger.info(f"Check request: sku={sku} ({type(sku)}) quantity={quantity}")
    if not isinstance(sku, str):
        logger.info('Invalid SKU type; returning 400')
        print(f"[DEBUG] invalid SKU type: {type(sku)} -> returning 400")
        return jsonify({'error': 'invalid sku'}), 400
    start = time.time()
    try:
        resp = requests.post(f"{V1_BASE}/api/v1/checkStock", json={'sku':sku, 'quantity': quantity}, timeout=5)
        latency = time.time() - start
        logger.info(f"V1 call latency: {latency:.3f}s status:{resp.status_code}")
        if resp.status_code == 200:
            body = resp.json()
            # Map v1 schema directly
            result = {
                'sku': body.get('sku'),
                'available': body.get('available', False),
                'quantity': body.get('quantity', 0),
                'note': 'v1'
            }
            return jsonify(result), 200
        elif resp.status_code == 400:
            # pass through validation errors from upstream
            logger.info('Upstream returned 400; passing through as 400')
            try:
                return jsonify(resp.json()), 400
            except Exception:
                return jsonify({'error': 'upstream bad request'}), 400
        else:
            return jsonify({'error':'upstream v1 error'}), 502
    except requests.exceptions.RequestException as e:
        logger.exception('v1 request failed')
        return jsonify({'error':'timeout'}), 504

@app.route('/', methods=['GET'])
def root():
    return 'cart service v1 ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('SERVICE_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
