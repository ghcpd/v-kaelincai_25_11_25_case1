from flask import Flask, request, jsonify
import time

app = Flask('v1mock')

CONFIG = {
    'delay': 0.0,
    'mode': 'normal'  # normal, zero, error, slow
}

@app.route('/api/v1/checkStock', methods=['POST'])
def check_stock():
    payload = request.get_json(force=True)
    time.sleep(CONFIG['delay'])
    if CONFIG['mode'] == 'error':
        return jsonify({'error':'internal'}), 500
    sku = payload.get('sku')
    if CONFIG['mode'] == 'zero':
        return jsonify({'sku': sku, 'available': False, 'quantity': 0, 'note': 'v1_zero'})
    # normal
    return jsonify({'sku': sku, 'available': True, 'quantity': 12, 'note': 'v1_confirmed'})

@app.route('/_admin/set_mode', methods=['POST'])
def set_mode():
    payload = request.get_json(force=True)
    CONFIG.update(payload)
    return jsonify({'ok': True, 'config': CONFIG})

@app.route('/_admin/reset', methods=['POST'])
def reset():
    CONFIG['delay'] = 0.0
    CONFIG['mode'] = 'normal'
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(port=5001)
