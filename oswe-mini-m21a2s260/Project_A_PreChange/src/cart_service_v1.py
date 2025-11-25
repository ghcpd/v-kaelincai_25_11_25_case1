import requests
import time

class CartServiceV1:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')

    def check_stock(self, sku):
        url = f"{self.base_url}/api/v1/checkStock"
        params = {"sku": sku}
        t0 = time.time()
        try:
            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()
            resp = r.json()
            # Legacy schema: {sku, available, quantity}
            return {
                "sku": resp.get("sku"),
                "available": bool(resp.get("available")),
                "quantity": int(resp.get("quantity", 0)),
                "note": "legacy"
            }, int((time.time()-t0)*1000)
        except Exception as e:
            return {"sku": sku, "available": False, "quantity": 0, "note": f"error:{e}"}, int((time.time()-t0)*1000)

if __name__ == '__main__':
    svc = CartServiceV1("http://localhost:5101")
    print(svc.check_stock("ABC123"))
