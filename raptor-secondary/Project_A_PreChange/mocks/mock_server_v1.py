import threading
import time
from flask import Flask, request, jsonify

# Simple in-memory responses keyed by SKU
RESPONSES = {
    "ABC123": {"available": True, "quantity": 12},
    "THRESH2": {"available": True, "quantity": 2},
    "PEND1": {"available": False, "quantity": 0},
    "BAD1": {"available": True, "quantity": 7},
    "ERR500": {"available": False, "quantity": 0},
}


def create_app():
    app = Flask(__name__)

    @app.route("/api/v1/checkStock", methods=["POST"])
    def check_stock():
        payload = request.get_json(force=True, silent=True) or {}
        sku = payload.get("sku")
        if not isinstance(sku, str):
            return jsonify({"error": "invalid sku"}), 400
        # Optional simulated latency
        delay_ms = payload.get("delay_ms")
        if isinstance(delay_ms, (int, float)) and delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        if sku == "ERR500":
            # Simulate server error
            return jsonify({"error": "internal"}), 500
        resp = RESPONSES.get(sku)
        if not resp:
            return jsonify({"available": False, "quantity": 0}), 200
        return jsonify(resp), 200

    return app


def run_mock(port: int = 5001):
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def start_in_thread(port: int = 5001):
    thread = threading.Thread(target=run_mock, kwargs={"port": port}, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    run_mock()
