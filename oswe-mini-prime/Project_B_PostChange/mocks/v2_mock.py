from flask import Flask, request, jsonify
import time
import threading
import os

app = Flask(__name__)

# internal map sku->status
state = {}

# default behaviors
DEFAULT_DELAY = float(os.environ.get('V2_DELAY', '0'))

@app.route('/api/v2/stock/availability', methods=['POST'])
def availability():
    body = request.json or {}
    sku = body.get('sku')
    regionId = body.get('regionId')
    warehouseGroup = body.get('warehouseGroup')
    # Behavior: if sku endswith 'P' -> pending, 'Z' -> not available, 'E' -> error
    if not isinstance(sku, str):
        return jsonify({'error':'invalid sku'}), 400
    if sku.endswith('P'):
        # initial pending response: returns availabilityStatus pending
        state[sku] = {'availabilityStatus': 'pending', 'sku': sku, 'available': False, 'quantity': 0}
        return jsonify({'sku': sku, 'availabilityStatus': 'pending', 'syncTimestamp': time.time() + 1}), 200
    elif sku.endswith('Z'):
        return jsonify({'sku': sku, 'availabilityStatus': 'confirmed', 'available': False, 'quantity': 0}), 200
    elif sku.endswith('E'):
        return jsonify({'error': 'boom'}), 500
    else:
        return jsonify({'sku': sku, 'availabilityStatus': 'confirmed', 'available': True, 'quantity': 10}), 200

@app.route('/api/v2/stock/status', methods=['POST'])
def status():
    body = request.json or {}
    sku = body.get('sku')
    s = state.get(sku)
    if s:
        # if pending, and more than 0.5s passed, explain we can flip to confirmed
        # For tests we'll expose admin endpoint to flip states
        return jsonify(s), 200
    return jsonify({'error':'unknown sku'}), 404

# Admin endpoints
@app.route('/_admin/set_status', methods=['POST'])
def admin_set_status():
    body = request.json or {}
    sku = body.get('sku')
    status = body.get('availabilityStatus')
    available = body.get('available', False)
    quantity = body.get('quantity', 0)
    if not sku:
        return jsonify({'error':'missing sku'}), 400
    state[sku] = {'availabilityStatus': status, 'sku': sku, 'available': available, 'quantity': quantity}
    return jsonify({'ok': True}), 200

@app.route('/_admin/reset', methods=['POST'])
def admin_reset():
    global state
    state = {}
    return jsonify({'ok': True}), 200

@app.route('/', methods=['GET'])
def root():
    return 'v2 mock ok', 200

if __name__ == '__main__':
    port = int(os.environ.get('V2_PORT', 6001))
    app.run(host='0.0.0.0', port=port)
