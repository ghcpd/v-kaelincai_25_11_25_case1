from flask import Flask, request, jsonify
import time

app = Flask('v2mock')

# store per-sku state
STATE = {}

CONFIG = {'delay': 0.0}

@app.route('/api/v2/stock/availability', methods=['POST'])
def availability():
    payload = request.get_json(force=True)
    sku = payload.get('sku')
    time.sleep(CONFIG['delay'])

    st = STATE.get(sku, {})
    mode = st.get('mode')

    if mode == 'confirmed':
        return jsonify({'sku': sku, 'available': True, 'quantity': 12, 'availabilityStatus': 'confirmed', 'syncTimestamp': st.get('syncTimestamp')}), 200

    if mode == 'confirmed_zero':
        return jsonify({'sku': sku, 'available': False, 'quantity': 0, 'availabilityStatus': 'confirmed', 'syncTimestamp': st.get('syncTimestamp')}), 200

    if mode == 'pending_then_confirm':
        # first call returns pending, later calls return confirmed
        calls = st.get('calls', 0)
        st['calls'] = calls + 1
        STATE[sku] = st
        if calls == 0:
            return jsonify({'sku': sku, 'available': False, 'quantity': 0, 'availabilityStatus': 'pending', 'syncTimestamp': st.get('syncTimestamp', '')}), 200
        else:
            return jsonify({'sku': sku, 'available': True, 'quantity': 7, 'availabilityStatus': 'confirmed', 'syncTimestamp': st.get('syncTimestamp', '')}), 200

    if mode == 'bad_input':
        return jsonify({'error': 'missing regionId or warehouseGroup'}), 400

    if mode == 'error_or_slow':
        # simulate a 500 or long delay
        if st.get('cause') == '500':
            return jsonify({'error': 'internal'}), 500
        time.sleep(2.5)
        return jsonify({'sku': sku, 'available': True, 'quantity': 12, 'availabilityStatus': 'confirmed'}), 200

    # default: confirmed
    return jsonify({'sku': sku, 'available': True, 'quantity': 12, 'availabilityStatus': 'confirmed'}), 200

@app.route('/_admin/set_state', methods=['POST'])
def set_state():
    payload = request.get_json(force=True)
    sku = payload['sku']
    STATE[sku] = payload
    return jsonify({'ok': True, 'state': STATE[sku]})

@app.route('/_admin/reset', methods=['POST'])
def reset():
    STATE.clear()
    CONFIG['delay'] = 0.0
    return jsonify({'ok': True})

@app.route('/_admin/set_config', methods=['POST'])
def set_config():
    payload = request.get_json(force=True)
    CONFIG.update(payload)
    return jsonify({'ok': True, 'config': CONFIG})

if __name__ == '__main__':
    app.run(port=6001)
