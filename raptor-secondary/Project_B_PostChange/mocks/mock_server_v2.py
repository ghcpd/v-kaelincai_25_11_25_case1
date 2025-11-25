import threading
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify

# State to simulate async pending -> confirmed transitions
REQUEST_COUNTS = {}

RESPONSES = {
    "ABC123": {"available": True, "quantity": 12, "availabilityStatus": "confirmed"},
    "THRESH2": {"available": True, "quantity": 2, "availabilityStatus": "confirmed"},
    # PEND1 will be handled dynamically to simulate pending then confirmed
    "PEND1": {},
    "BAD1": {"available": False, "quantity": 0, "availabilityStatus": "invalid"},
    "ERR500": {"available": False, "quantity": 0, "availabilityStatus": "error"},
}


def create_app():
    app = Flask(__name__)

    @app.route("/api/v2/stock/availability", methods=["POST"])
    def stock_availability():
        payload = request.get_json(force=True, silent=True) or {}
        sku = payload.get("sku")
        region_id = payload.get("regionId")
        warehouse_group = payload.get("warehouseGroup")
        delay_ms = payload.get("delay_ms") or 0

        if not isinstance(sku, str):
            return jsonify({"error": "invalid sku"}), 400
        if not region_id or not warehouse_group:
            return jsonify({"error": "missing region or warehouse"}), 400

        # Simulate latency
        if isinstance(delay_ms, (int, float)) and delay_ms > 0:
            time.sleep(delay_ms / 1000.0)

        # Async simulation for PEND1
        if sku == "PEND1":
            key = (sku, region_id, warehouse_group)
            count = REQUEST_COUNTS.get(key, 0)
            REQUEST_COUNTS[key] = count + 1
            if count == 0:
                # first response: pending
                return jsonify({
                    "sku": sku,
                    "available": False,
                    "quantity": None,
                    "availabilityStatus": "pending",
                    "syncTimestamp": datetime.now(timezone.utc).isoformat(),
                }), 200
            else:
                # subsequent response: confirmed
                return jsonify({
                    "sku": sku,
                    "available": True,
                    "quantity": 5,
                    "availabilityStatus": "confirmed",
                    "syncTimestamp": datetime.now(timezone.utc).isoformat(),
                }), 200

        if sku == "ERR500":
            # Simulate high latency/hard error
            time.sleep(1.0)
            return jsonify({"error": "upstream failure"}), 500

        resp = RESPONSES.get(sku)
        if not resp:
            return jsonify({
                "sku": sku,
                "available": False,
                "quantity": 0,
                "availabilityStatus": "not_found",
                "syncTimestamp": datetime.now(timezone.utc).isoformat(),
            }), 200

        body = {
            "sku": sku,
            "available": resp.get("available", False),
            "quantity": resp.get("quantity", 0),
            "availabilityStatus": resp.get("availabilityStatus", "confirmed"),
            "syncTimestamp": datetime.now(timezone.utc).isoformat(),
        }
        return jsonify(body), 200

    return app


def run_mock(port: int = 5002):
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def start_in_thread(port: int = 5002):
    thread = threading.Thread(target=run_mock, kwargs={"port": port}, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    run_mock()
