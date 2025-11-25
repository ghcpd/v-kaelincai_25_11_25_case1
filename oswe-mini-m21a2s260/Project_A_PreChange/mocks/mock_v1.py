from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

@app.route('/api/v1/checkStock')
def check_stock():
    sku = request.args.get('sku')
    # Simulated behaviors via query flags
    mode = request.args.get('mode', 'normal')
    if mode == 'delay':
        time.sleep(1.2)
    if mode == 'error':
        return jsonify({"error":"internal"}), 500
    if sku is None:
        return jsonify({"error":"missing sku"}), 400
    # Basic deterministic available
    if sku.endswith('ZERO'):
        return jsonify({"sku":sku, "available": False, "quantity": 0})
    return jsonify({"sku":sku, "available": True, "quantity": 10})

if __name__ == '__main__':
    port = int(os.environ.get('MOCK_V1_PORT', 5101))
    app.run(port=port)
