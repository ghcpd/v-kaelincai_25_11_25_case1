import time
import requests

class CartServiceV2:
    def __init__(self, base_url, region='ap-sg-1', warehouse_group='WG-2', poll_timeout=5):
        self.base_url = base_url.rstrip('/')
        self.region = region
        self.warehouse_group = warehouse_group
        self.poll_timeout = poll_timeout

    def check_stock(self, sku):
        url = f"{self.base_url}/api/v2/stock/availability"
        payload = {"sku": sku, "regionId": self.region, "warehouseGroup": self.warehouse_group}
        t0 = time.time()
        try:
            r = requests.post(url, json=payload, timeout=5)
            r.raise_for_status()
            data = r.json()
            # v2 can return availabilityStatus: 'confirmed' or 'pending'
            status = data.get('availabilityStatus', 'confirmed')
            if status == 'confirmed':
                return {
                    'sku': data.get('sku'),
                    'available': bool(data.get('available')), 
                    'quantity': int(data.get('quantity', 0)),
                    'note': 'confirmed'
                }, int((time.time()-t0)*1000)
            # if pending, poll until syncTimestamp or timeout
            sync_ts = data.get('syncTimestamp')
            deadline = time.time() + self.poll_timeout
            while time.time() < deadline:
                time.sleep(0.5)
                r2 = requests.get(url, params={'sku':sku, 'regionId': self.region, 'warehouseGroup': self.warehouse_group}, timeout=3)
                if r2.status_code != 200:
                    break
                d2 = r2.json()
                if d2.get('availabilityStatus') == 'confirmed':
                    return {
                        'sku': d2.get('sku'),
                        'available': bool(d2.get('available')),
                        'quantity': int(d2.get('quantity', 0)),
                        'note': 'confirmed-after-poll'
                    }, int((time.time()-t0)*1000)
            # fallback
            return {'sku': sku, 'available': False, 'quantity': 0, 'note': 'pending-timeout'}, int((time.time()-t0)*1000)

        except Exception as e:
            # fallback mode: return unavailable but log note
            return {'sku': sku, 'available': False, 'quantity': 0, 'note': f'error:{e}'}, int((time.time()-t0)*1000)

if __name__ == '__main__':
    svc = CartServiceV2('http://localhost:5201')
    print(svc.check_stock('ABC123'))
