"""
API Adapter - Compatibility Layer
Provides fallback, circuit breaker, and v1/v2 migration support
"""
import requests
import logging
import time
from typing import Dict, Optional
from collections import deque
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker for API calls"""
    
    def __init__(self, failure_threshold: int = 3, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.failures = deque(maxlen=failure_threshold)
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = None
    
    def record_failure(self):
        """Record a failure"""
        now = datetime.now()
        self.failures.append(now)
        self.last_failure_time = now
        
        if len(self.failures) >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_threshold} failures")
    
    def record_success(self):
        """Record a success"""
        self.failures.clear()
        self.state = "CLOSED"
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state == "CLOSED":
            return False
        
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time and datetime.now() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker entering HALF_OPEN state")
                return False
            return True
        
        # HALF_OPEN - allow one request through
        return False


class APIAdapter:
    """
    Adapter for v1/v2 API compatibility
    Provides fallback, validation, and circuit breaker
    """
    
    def __init__(
        self, 
        v2_base_url: str = "http://localhost:5002",
        v1_base_url: str = "http://localhost:5001",
        enable_fallback: bool = True,
        timeout: int = 5
    ):
        self.v2_base_url = v2_base_url
        self.v1_base_url = v1_base_url
        self.enable_fallback = enable_fallback
        self.timeout = timeout
        
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=60)
        self.fallback_count = 0
        self.retry_count = 0
    
    def check_availability(
        self, 
        sku: str, 
        quantity: int = 1,
        region_id: Optional[str] = None,
        warehouse_group: Optional[str] = None
    ) -> Dict:
        """
        Check availability with v2 API and optional v1 fallback
        """
        start_time = time.time()
        
        # Validate parameters for v2
        validation_error = self._validate_v2_params(sku, region_id, warehouse_group)
        if validation_error:
            logger.error(f"Validation error: {validation_error}")
            
            # Fallback to v1 if enabled
            if self.enable_fallback:
                logger.info("Attempting fallback to v1 API")
                return self._fallback_to_v1(sku, quantity, start_time, validation_error)
            
            return {
                "available": False,
                "quantity": 0,
                "note": "validation_error",
                "status_code": 400,
                "latency_ms": 0,
                "api_version": "v2",
                "error": validation_error,
                "fallback": False
            }
        
        # Check circuit breaker
        if self.circuit_breaker.is_open():
            logger.warning("Circuit breaker is OPEN, falling back to v1")
            if self.enable_fallback:
                return self._fallback_to_v1(sku, quantity, start_time, "Circuit breaker open")
            
            return {
                "available": False,
                "quantity": 0,
                "note": "circuit_breaker_open",
                "status_code": 503,
                "latency_ms": 0,
                "api_version": "v2",
                "error": "Service temporarily unavailable",
                "fallback": False
            }
        
        # Try v2 API
        try:
            result = self._call_v2_api(sku, quantity, region_id, warehouse_group, start_time)
            
            if result["status_code"] == 200:
                self.circuit_breaker.record_success()
                return result
            
            # Handle errors
            if result["status_code"] >= 500:
                self.circuit_breaker.record_failure()
                
                # Retry once for 5xx errors
                if result.get("retryable", False):
                    logger.info("Retrying request after 5xx error")
                    self.retry_count += 1
                    time.sleep(0.5)  # Brief delay
                    retry_result = self._call_v2_api(sku, quantity, region_id, warehouse_group, time.time())
                    
                    if retry_result["status_code"] == 200:
                        self.circuit_breaker.record_success()
                        return retry_result
                
                # Fallback to v1
                if self.enable_fallback:
                    logger.info("Falling back to v1 API after v2 error")
                    return self._fallback_to_v1(sku, quantity, start_time, result.get("error", "v2 API error"))
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in adapter: {str(e)}")
            self.circuit_breaker.record_failure()
            
            if self.enable_fallback:
                return self._fallback_to_v1(sku, quantity, start_time, str(e))
            
            return {
                "available": False,
                "quantity": 0,
                "note": "exception",
                "status_code": 500,
                "latency_ms": (time.time() - start_time) * 1000,
                "api_version": "v2",
                "error": str(e),
                "fallback": False
            }
    
    def _validate_v2_params(
        self, 
        sku: str, 
        region_id: Optional[str], 
        warehouse_group: Optional[str]
    ) -> Optional[str]:
        """Validate v2 API parameters"""
        if not sku:
            return "Missing required parameter: sku"
        if not region_id:
            return "Missing required parameter: regionId"
        if not warehouse_group:
            return "Missing required parameter: warehouseGroup"
        return None
    
    def _call_v2_api(
        self, 
        sku: str, 
        quantity: int,
        region_id: str,
        warehouse_group: str,
        start_time: float
    ) -> Dict:
        """Call v2 API directly"""
        url = f"{self.v2_base_url}/api/v2/stock/availability"
        payload = {
            "sku": sku,
            "regionId": region_id,
            "warehouseGroup": warehouse_group,
            "quantity": quantity
        }
        
        response = requests.post(url, json=payload, timeout=self.timeout)
        elapsed = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            available = data.get("available", False)
            stock_quantity = data.get("quantity", 0)
            availability_status = data.get("availabilityStatus", "unknown")
            at_threshold = data.get("atThreshold", False)
            
            requires_polling = availability_status == "pending"
            
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
                "syncTimestamp": data.get("syncTimestamp", ""),
                "requiresPolling": requires_polling,
                "fallback": False
            }
            
            if requires_polling:
                result["estimatedSyncTime"] = data.get("estimatedSyncTime", 5)
            
            return result
        
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", response.text)
            except:
                error_msg = response.text
            
            return {
                "available": False,
                "quantity": 0,
                "note": "service_error" if response.status_code >= 500 else "api_error",
                "status_code": response.status_code,
                "latency_ms": round(elapsed, 2),
                "api_version": "v2",
                "error": error_msg,
                "fallback": False,
                "retryable": response.status_code >= 500
            }
    
    def _fallback_to_v1(
        self, 
        sku: str, 
        quantity: int, 
        start_time: float,
        reason: str
    ) -> Dict:
        """Fallback to v1 API"""
        logger.info(f"Executing fallback to v1 API. Reason: {reason}")
        self.fallback_count += 1
        
        try:
            url = f"{self.v1_base_url}/api/v1/checkStock"
            payload = {"sku": sku}
            
            response = requests.post(url, json=payload, timeout=self.timeout)
            elapsed = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                available = data.get("available", False)
                stock = data.get("stock", 0)
                
                result = {
                    "available": available and stock >= quantity,
                    "quantity": stock,
                    "note": "fallback_success",
                    "status_code": 200,
                    "latency_ms": round(elapsed, 2),
                    "api_version": "v1",
                    "fallback": True,
                    "fallback_reason": reason
                }
                
                logger.info(f"Fallback successful: {result}")
                return result
            
            else:
                return {
                    "available": False,
                    "quantity": 0,
                    "note": "fallback_failed",
                    "status_code": response.status_code,
                    "latency_ms": round(elapsed, 2),
                    "api_version": "v1",
                    "fallback": True,
                    "fallback_reason": reason,
                    "error": response.text
                }
        
        except Exception as e:
            elapsed = (time.time() - start_time) * 1000
            logger.error(f"Fallback to v1 failed: {str(e)}")
            return {
                "available": False,
                "quantity": 0,
                "note": "fallback_exception",
                "status_code": 500,
                "latency_ms": round(elapsed, 2),
                "api_version": "v1",
                "fallback": True,
                "fallback_reason": reason,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict:
        """Get adapter statistics"""
        return {
            "fallback_count": self.fallback_count,
            "retry_count": self.retry_count,
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": len(self.circuit_breaker.failures)
        }
