import requests
import time
from typing import Dict, Any

class CartServiceV1:
    """Legacy cart service that calls /api/v1/checkStock with only sku"""

    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def check_stock(self, sku: str) -> Dict[str, Any]:
        resp = requests.post(f"{self.base_url}/api/v1/checkStock", json={"sku": sku}, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        # legacy response assumed shape: {sku, available, quantity}
        out = {
            "sku": data.get("sku"),
            "available": bool(data.get("available")),
            "quantity": int(data.get("quantity", 0)),
            "note": data.get("note", "v1")
        }
        return out


if __name__ == '__main__':
    import sys
    base = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:5001'
    svc = CartServiceV1(base)
    print(svc.check_stock('ABC123'))
