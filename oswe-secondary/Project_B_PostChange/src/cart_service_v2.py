import requests
import time
from typing import Dict, Any

class CartServiceV2:
    """Service that uses /api/v2/stock/availability and gracefully falls back to v1 when necessary."""

    def __init__(self, base_v2: str, base_v1: str = None, timeout: float = 3.0, poll_interval: float = 0.5, poll_timeout: float = 5.0):
        self.base_v2 = base_v2.rstrip('/')
        self.base_v1 = base_v1.rstrip('/') if base_v1 else None
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def _call_v2(self, payload: Dict[str, Any]):
        resp = requests.post(f"{self.base_v2}/api/v2/stock/availability", json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _call_v1(self, sku: str):
        if not self.base_v1:
            raise RuntimeError('No v1 backend configured')
        resp = requests.post(f"{self.base_v1}/api/v1/checkStock", json={"sku": sku}, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def check_stock(self, sku: str, regionId: str = None, warehouseGroup: str = None) -> Dict[str, Any]:
        # Validate inputs
        payload = {"sku": sku}
        if regionId:
            payload['regionId'] = regionId
        if warehouseGroup:
            payload['warehouseGroup'] = warehouseGroup

        # If missing required params, fall back to v1
        if not regionId or not warehouseGroup:
            if self.base_v1:
                v1 = self._call_v1(sku)
                return {"sku": v1.get('sku'), "available": bool(v1.get('available')), "quantity": int(v1.get('quantity',0)), "note": "used_v1_fallback"}
            else:
                raise ValueError('Missing regionId/warehouseGroup and no v1 fallback configured')

        try:
            resp = self._call_v2(payload)
        except Exception:
            # fallback on network errors or non-200
            if self.base_v1:
                v1 = self._call_v1(sku)
                return {"sku": v1.get('sku'), "available": bool(v1.get('available')), "quantity": int(v1.get('quantity',0)), "note": "v2_error_fallback"}
            raise

        status = resp.get('availabilityStatus')
        if status == 'confirmed':
            return {"sku": resp.get('sku'), "available": bool(resp.get('available')), "quantity": int(resp.get('quantity',0)), "note": resp.get('availabilityStatus')}

        # handle async pending status by polling until confirmed or timeout
        if status == 'pending':
            start = time.time()
            while time.time() - start < self.poll_timeout:
                time.sleep(self.poll_interval)
                try:
                    follow = self._call_v2(payload)
                except Exception:
                    break
                if follow.get('availabilityStatus') == 'confirmed':
                    return {"sku": follow.get('sku'), "available": bool(follow.get('available')), "quantity": int(follow.get('quantity',0)), "note": 'confirmed_after_poll'}

        # If we reached here, not confirmed — fallback to v1 if available, else return partial
        if self.base_v1:
            v1 = self._call_v1(sku)
            return {"sku": v1.get('sku'), "available": bool(v1.get('available')), "quantity": int(v1.get('quantity',0)), "note": "used_v1_fallback"}

        return {"sku": resp.get('sku'), "available": bool(resp.get('available', False)), "quantity": int(resp.get('quantity',0)), "note": resp.get('availabilityStatus')}


if __name__ == '__main__':
    import os, sys
    v2 = os.environ.get('V2_MOCK', 'http://localhost:6001')
    v1 = os.environ.get('V1_MOCK', 'http://localhost:5001')
    svc = CartServiceV2(v2, v1)
    print(svc.check_stock('ABC123', regionId='ap-sg-1', warehouseGroup='WG-2'))
