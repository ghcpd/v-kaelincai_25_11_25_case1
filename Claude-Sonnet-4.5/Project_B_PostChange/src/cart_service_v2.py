"""
Cart Service v2 - New API Integration
Uses /api/v2/stock/availability endpoint (region-aware, async-capable)
"""
import requests
import logging
import time
from typing import Dict, Optional
from adapter import APIAdapter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CartServiceV2:
    """Shopping cart service using new v2 stock API with region awareness"""
    
    def __init__(
        self, 
        api_base_url: str = "http://localhost:5002",
        use_adapter: bool = True,
        enable_fallback: bool = True
    ):
        self.api_base_url = api_base_url
        self.timeout = 5  # seconds
        self.use_adapter = use_adapter
        self.enable_fallback = enable_fallback
        
        if use_adapter:
            self.adapter = APIAdapter(
                v2_base_url=api_base_url,
                enable_fallback=enable_fallback
            )
    
    def check_availability(
        self, 
        sku: str, 
        quantity: int = 1,
        region_id: Optional[str] = None,
        warehouse_group: Optional[str] = None
    ) -> Dict:
        """
        Check stock availability using v2 API
        
        Args:
            sku: Product SKU
            quantity: Requested quantity
            region_id: Region identifier (required for v2)
            warehouse_group: Warehouse group (required for v2)
            
        Returns:
            Dict with availability decision and metadata
        """
        start_time = time.time()
        
        # Use adapter if enabled
        if self.use_adapter:
            return self.adapter.check_availability(
                sku=sku,
                quantity=quantity,
                region_id=region_id,
                warehouse_group=warehouse_group
            )
        
        # Direct v2 API call (no adapter)
        return self._call_v2_api(sku, quantity, region_id, warehouse_group, start_time)
    
    def _call_v2_api(
        self, 
        sku: str, 
        quantity: int,
        region_id: Optional[str],
        warehouse_group: Optional[str],
        start_time: float
    ) -> Dict:
        """Direct v2 API call without adapter"""
        
        try:
            logger.info(f"Checking stock for SKU: {sku}, region: {region_id}, warehouse: {warehouse_group}")
            
            # Validate required parameters
            if not region_id:
                logger.error("Missing required parameter: regionId")
                return {
                    "available": False,
                    "quantity": 0,
                    "note": "validation_error",
                    "status_code": 400,
                    "latency_ms": 0,
                    "api_version": "v2",
                    "error": "Missing required parameter: regionId",
                    "fallback": False
                }
            
            if not warehouse_group:
                logger.error("Missing required parameter: warehouseGroup")
                return {
                    "available": False,
                    "quantity": 0,
                    "note": "validation_error",
                    "status_code": 400,
                    "latency_ms": 0,
                    "api_version": "v2",
                    "error": "Missing required parameter: warehouseGroup",
                    "fallback": False
                }
            
            # Call v2 API
            url = f"{self.api_base_url}/api/v2/stock/availability"
            payload = {
                "sku": sku,
                "regionId": region_id,
                "warehouseGroup": warehouse_group,
                "quantity": quantity
            }
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            
            elapsed = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse v2 response
                available = data.get("available", False)
                stock_quantity = data.get("quantity", 0)
                availability_status = data.get("availabilityStatus", "unknown")
                sync_timestamp = data.get("syncTimestamp", "")
                at_threshold = data.get("atThreshold", False)
                
                # Handle async/pending cases
                requires_polling = availability_status == "pending"
                
                # Determine note
                if at_threshold:
                    note = "confirmed_at_threshold"
                elif requires_polling:
                    note = "pending_sync"
                else:
                    note = "confirmed"
                
                result = {
                    "available": available and stock_quantity >= quantity,
                    "quantity": stock_quantity,
                    "note": note,
                    "status_code": 200,
                    "latency_ms": round(elapsed, 2),
                    "api_version": "v2",
                    "availabilityStatus": availability_status,
                    "syncTimestamp": sync_timestamp,
                    "requiresPolling": requires_polling,
                    "fallback": False
                }
                
                if requires_polling:
                    result["estimatedSyncTime"] = data.get("estimatedSyncTime", 5)
                
                logger.info(f"Stock check result: {result}")
                return result
                
            else:
                # Error handling
                logger.error(f"API error: status={response.status_code}")
                
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", response.text)
                except:
                    error_msg = response.text
                
                return {
                    "available": False,
                    "quantity": 0,
                    "note": "api_error" if response.status_code < 500 else "service_error",
                    "status_code": response.status_code,
                    "latency_ms": round(elapsed, 2),
                    "api_version": "v2",
                    "error": error_msg,
                    "fallback": False,
                    "retryable": response.status_code >= 500
                }
                
        except requests.Timeout:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"Request timeout after {elapsed}ms")
            return {
                "available": False,
                "quantity": 0,
                "note": "timeout",
                "status_code": 504,
                "latency_ms": round(elapsed, 2),
                "api_version": "v2",
                "error": "Request timeout",
                "fallback": False,
                "retryable": True
            }
            
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "available": False,
                "quantity": 0,
                "note": "exception",
                "status_code": 500,
                "latency_ms": round(elapsed, 2),
                "api_version": "v2",
                "error": str(e),
                "fallback": False
            }


def main():
    """Demo usage"""
    service = CartServiceV2(use_adapter=True, enable_fallback=True)
    
    # Example checks
    result1 = service.check_availability(
        "ABC123", 
        quantity=5, 
        region_id="ap-sg-1", 
        warehouse_group="WG-2"
    )
    print(f"Result 1: {result1}")
    
    result2 = service.check_availability(
        "XYZ789", 
        quantity=1,
        region_id="us-east-1",
        warehouse_group="WG-1"
    )
    print(f"Result 2: {result2}")


if __name__ == "__main__":
    main()
