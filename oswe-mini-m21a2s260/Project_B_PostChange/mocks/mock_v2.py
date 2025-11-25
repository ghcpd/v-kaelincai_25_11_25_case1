from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

STORE = {}

@app.route('/api/v2/stock/availability', methods=['POST', 'GET'])
def availability():
    if request.method == 'POST':
        body = request.get_json(force=True)
        sku = body.get('sku')
        region = body.get('regionId')
        wg = body.get('warehouseGroup')
        # behavior override via sku suffix
        if sku is None:
            return jsonify({"error":"missing sku"}), 400
        if sku.endswith('BADWG'):
            return jsonify({"error":"invalid warehouseGroup"}), 400
        # pending case
        if sku.endswith('PEND'):
            # store as pending, return pending with syncTimestamp in the future
            STORE[sku] = {'sku':sku, 'available':True, 'quantity':5, 'availabilityStatus':'pending'}
            return jsonify({'sku':sku, 'availabilityStatus':'pending', 'quantity':5, 'syncTimestamp':'2025-12-01T12:00:00Z'})
        # immediate confirmed
        if sku.endswith('ZERO'):
            return jsonify({'sku':sku, 'available':False, 'quantity':0, 'availabilityStatus':'confirmed'})
        return jsonify({'sku':sku, 'available':True, 'quantity':12, 'availabilityStatus':'confirmed'})
    else:
        # GET polling status
        sku = request.args.get('sku')
        if not sku:
            return jsonify({'error':'missing sku'}), 400
        if sku in STORE:
            # simulate eventual confirmation after some time
            entry = STORE[sku]
            # Flip to confirmed for testing
            entry['availabilityStatus'] = 'confirmed'
            return jsonify({'sku':sku, 'available':entry['available'], 'quantity':entry['quantity'], 'availabilityStatus':'confirmed'})
        return jsonify({'error':'not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('MOCK_V2_PORT', 5201))
    app.run(port=port)
