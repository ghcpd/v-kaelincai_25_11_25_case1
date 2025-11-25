"""
Cart Service v1 - Legacy Integration
Uses /api/v1/checkStock endpoint (simple stock check)
"""
import requests
import logging
import time
from typing import Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CartServiceV1:
    """Shopping cart service using legacy v1 stock API"""
    
    def __init__(self, api_base_url: str = "http://localhost:5001"):
        self.api_base_url = api_base_url
        self.timeout = 5  # seconds
        
    def check_availability(self, sku: str, quantity: int = 1) -> Dict:
        """
        Check stock availability using v1 API
        
        Args:
            sku: Product SKU
            quantity: Requested quantity
            
        Returns:
            Dict with availability decision and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Checking stock for SKU: {sku}, quantity: {quantity}")
            
            # Call v1 API
            url = f"{self.api_base_url}/api/v1/checkStock"
            payload = {"sku": sku}
            
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            
            elapsed = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                data = response.json()
                available = data.get("available", False)
                stock = data.get("stock", 0)
                
                # Simple availability logic
                result = {
                    "available": available and stock >= quantity,
                    "quantity": stock,
                    "note": "confirmed",
                    "status_code": 200,
                    "latency_ms": round(elapsed, 2),
                    "api_version": "v1"
                }
                
                logger.info(f"Stock check result: {result}")
                return result
                
            else:
                # Error handling
                logger.error(f"API error: status={response.status_code}")
                return {
                    "available": False,
                    "quantity": 0,
                    "note": "api_error",
                    "status_code": response.status_code,
                    "latency_ms": round(elapsed, 2),
                    "api_version": "v1",
                    "error": response.text
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
                "api_version": "v1",
                "error": "Request timeout"
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
                "api_version": "v1",
                "error": str(e)
            }


def main():
    """Demo usage"""
    service = CartServiceV1()
    
    # Example checks
    result1 = service.check_availability("ABC123", quantity=5)
    print(f"Result 1: {result1}")
    
    result2 = service.check_availability("XYZ789", quantity=1)
    print(f"Result 2: {result2}")


if __name__ == "__main__":
    main()
