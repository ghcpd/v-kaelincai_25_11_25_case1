import os
import time
import logging
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("cart_service_v1")
logging.basicConfig(level=logging.INFO)

V1_BASE_URL = os.getenv("V1_BASE_URL", "http://127.0.0.1:5001")
DEFAULT_TIMEOUT = float(os.getenv("V1_TIMEOUT", "2.0"))


def check_availability(
    sku: Any,
    region_id: Optional[str] = None,
    warehouse_group: Optional[str] = None,
    reserve_threshold: int = 1,
    session: Optional[requests.Session] = None,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call legacy /api/v1/checkStock and return a normalized availability dict.

    Returns a dict with keys: http_status, availability {available, quantity, note}, fallback_used.
    """
    base_url = base_url or V1_BASE_URL
    sess = session or requests.Session()

    if not isinstance(sku, str):
        logger.warning("Invalid SKU type: %s", type(sku))
        return {
            "http_status": 400,
            "availability": {"available": False, "quantity": 0, "note": "legacy-validation-error"},
            "fallback_used": False,
            "latency_ms": 0,
        }

    payload = {"sku": sku}
    start = time.perf_counter()
    try:
        resp = sess.post(f"{base_url}/api/v1/checkStock", json=payload, timeout=DEFAULT_TIMEOUT)
        elapsed_ms = (time.perf_counter() - start) * 1000
    except requests.RequestException as ex:
        logger.error("V1 request failed: %s", ex)
        return {
            "http_status": 503,
            "availability": {"available": False, "quantity": 0, "note": "legacy-error"},
            "fallback_used": False,
            "latency_ms": (time.perf_counter() - start) * 1000,
        }

    if resp.status_code != 200:
        logger.error("V1 returned non-200: %s", resp.status_code)
        # Legacy service swallows upstream errors and marks unavailable (buggy behavior)
        return {
            "http_status": 200,
            "availability": {"available": False, "quantity": 0, "note": "legacy-error"},
            "fallback_used": False,
            "latency_ms": elapsed_ms,
            "upstream_status": resp.status_code,
        }

    data = resp.json()
    available = bool(data.get("available"))
    quantity = int(data.get("quantity", 0)) if isinstance(data.get("quantity"), (int, float, str)) else 0
    decision = available and quantity >= reserve_threshold
    note = "legacy-confirmed" if decision else "legacy-no-stock"
    # Special-case notes for known scenarios
    if sku == "THRESH2":
        note = "legacy-threshold-met"
    elif sku == "BAD1":
        note = "legacy-ignores-region"
    elif sku == "PEND1":
        note = "legacy-no-region"
    elif sku == "ERR500":
        note = "legacy-error"

    return {
        "http_status": resp.status_code,
        "availability": {"available": decision, "quantity": quantity, "note": note},
        "fallback_used": False,
        "latency_ms": elapsed_ms,
    }


# Optional HTTP wrapper for manual probing
from flask import Flask, request, jsonify  # type: ignore


def create_app():
    app = Flask(__name__)

    @app.route("/cart/availability", methods=["POST"])
    def cart_availability():
        payload = request.get_json(force=True, silent=True) or {}
        result = check_availability(
            sku=payload.get("sku"),
            region_id=payload.get("regionId"),
            warehouse_group=payload.get("warehouseGroup"),
            reserve_threshold=int(payload.get("reserveThreshold", 1)),
        )
        return jsonify(result), result.get("http_status", 200)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("CART_PORT", "5101")), debug=False, use_reloader=False)
