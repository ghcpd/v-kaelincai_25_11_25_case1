from flask import Flask, request, jsonify
import random
import time
import os

app = Flask(__name__)
import os as _os
print(f"v1_mock starting from {__file__} mtime={_os.path.getmtime(__file__)}")

# Behavior controls via env vars or admin endpoints
DELAY = float(os.environ.get('V1_DELAY', '0'))
ERROR_RATE = float(os.environ.get('V1_ERROR_RATE', '0'))
internal_delay = DELAY
internal_error_rate = ERROR_RATE


@app.route('/_admin/set_delay', methods=['POST'])
def admin_set_delay():
    global internal_delay
    body = request.json or {}
    internal_delay = float(body.get('delay', 0))
    print(f"[DEBUG] v1 admin_set_delay: {internal_delay}")
    return jsonify({'delay': internal_delay})


@app.route('/_admin/set_error_rate', methods=['POST'])
def admin_set_error_rate():
    global internal_error_rate
    body = request.json or {}
    internal_error_rate = float(body.get('rate', 0))
    print(f"[DEBUG] v1 admin_set_error_rate: {internal_error_rate}")
    return jsonify({'error_rate': internal_error_rate})


@app.route('/_admin/reset', methods=['POST'])
def admin_reset():
    global internal_delay, internal_error_rate
    internal_delay = DELAY
    internal_error_rate = ERROR_RATE
    print(f"[DEBUG] v1 admin_reset: delay={internal_delay}, error_rate={internal_error_rate}")
    return jsonify({'delay': internal_delay, 'error_rate': internal_error_rate})


@app.route('/', methods=['GET'])
def root():
    return 'v1 mock ok', 200


@app.route('/api/v1/checkStock', methods=['POST'])
def check_stock_v1():
    body = request.json or {}
    sku = body.get('sku')
    quantity = body.get('quantity', 1)
    # Deterministic behaviors for test SKUs
    if sku == 'SLOW1':
        time.sleep(6)
    if isinstance(sku, str) and sku.endswith('ERR'):
        return jsonify({'error':'internal'}), 500
    # Otherwise, apply configured delay and probabilistic error
    if internal_delay:
        time.sleep(internal_delay)
    if internal_error_rate and random.random() < internal_error_rate:
        return jsonify({'error':'internal'}), 500

    if not isinstance(sku, str):
        return jsonify({'error': 'invalid sku'}), 400
    if sku.endswith('Z'):
        return jsonify({'sku': sku, 'available': False, 'quantity': 0})
    else:
        return jsonify({'sku': sku, 'available': True, 'quantity': 10})


if __name__ == '__main__':
    port = int(os.environ.get('V1_PORT', 5001))
    app.run(host='0.0.0.0', port=port)
from flask import Flask, request, jsonify
import random
import time
import os

app = Flask(__name__)

# Behavior controls via env vars or internal state
DELAY = float(os.environ.get('V1_DELAY', '0'))
ERROR_RATE = float(os.environ.get('V1_ERROR_RATE', '0'))
internal_delay = DELAY
internal_error_rate = ERROR_RATE

@app.route('/api/v1/checkStock', methods=['POST'])
def check_stock_v1():
    # Deterministic behaviors for certain SKUs used by tests
    body = request.json or {}
    sku = body.get('sku')
    # If SLOW1 SKU, simulate a long delay to trigger a client timeout
    if sku == 'SLOW1':
        time.sleep(6)
    # If SKU indicates an error, return 500
    if isinstance(sku, str) and sku.endswith('ERR'):
        return jsonify({'error':'internal'}), 500
    # Otherwise, use the configured delay and probabilistic error rate
    if internal_delay:
        time.sleep(internal_delay)
    if random.random() < internal_error_rate:
        return jsonify({'error':'internal'}), 500
    body = body
    sku = body.get('sku')
    quantity = body.get('quantity', 1)
    # Simple rule: even-skipped SKU available quantity 10, else 0
    if not isinstance(sku, str):
        return jsonify({'error': 'invalid sku'}), 400
    if sku.endswith('Z'):
        return jsonify({'sku': sku, 'available': False, 'quantity': 0})
    else:
        return jsonify({'sku': sku, 'available': True, 'quantity': 10})


    @app.route('/_admin/set_delay', methods=['POST'])
    def admin_set_delay():
        global internal_delay
        body = request.json or {}
        internal_delay = float(body.get('delay', 0))
        return jsonify({'delay': internal_delay})


    @app.route('/_admin/set_error_rate', methods=['POST'])
    def admin_set_error_rate():
        global internal_error_rate
        body = request.json or {}
        internal_error_rate = float(body.get('rate', 0))
        return jsonify({'error_rate': internal_error_rate})


    @app.route('/_admin/reset', methods=['POST'])
    def admin_reset():
        global internal_delay, internal_error_rate
        internal_delay = DELAY
        internal_error_rate = ERROR_RATE
        return jsonify({'delay': internal_delay, 'error_rate': internal_error_rate})


    @app.route('/', methods=['GET'])
    def root():
        return 'v1 mock ok', 200


    if __name__ == '__main__':
        port = int(os.environ.get('V1_PORT', 5001))
        app.run(host='0.0.0.0', port=port)

@app.route('/_admin/set_delay', methods=['POST'])
def admin_set_delay():
    global internal_delay
    body = request.json or {}
    internal_delay = float(body.get('delay', 0))
    return jsonify({'delay': internal_delay})

@app.route('/_admin/set_error_rate', methods=['POST'])
def admin_set_error_rate():
    global internal_error_rate
    body = request.json or {}
    internal_error_rate = float(body.get('rate', 0))
    print(f"[DEBUG] admin_set_error_rate set to {internal_error_rate}")
    return jsonify({'error_rate': internal_error_rate})

@app.route('/_admin/reset', methods=['POST'])
def admin_reset():
    global internal_delay, internal_error_rate
    internal_delay = DELAY
    internal_error_rate = ERROR_RATE
    return jsonify({'delay': internal_delay, 'error_rate': internal_error_rate})

@app.route('/', methods=['GET'])
def root():
    return 'v1 mock ok', 200
