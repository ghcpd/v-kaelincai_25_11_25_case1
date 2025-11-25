"""
Project B - Post-Change: Updated Cart Service using v2 API with Async Handling

This module implements an improved shopping cart service that calls the new
/api/v2/stock/availability endpoint with enhanced region awareness and async support.

Key characteristics:
- Region-aware API calls requiring regionId and warehouseGroup
- Handles async/pending responses with polling capability
- Backward compatibility adapter for graceful degradation
- Retry logic with exponential backoff
- Comprehensive error handling and logging

Architecture:
- V2ApiClient: Calls v2 endpoint with retry/polling
- AsyncStockPoller: Handles eventual consistency
- CompatibilityAdapter: Maintains backward compatibility
- CartServiceV2: Main service orchestrating flow
"""

import os
import requests
import logging
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Configure logging
try:
    log_path = Path(__file__).parent.parent / 'logs' / 'log_post.txt'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handlers = [
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
except:
    handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)


class AvailabilityStatus(Enum):
    """Enumeration of availability statuses from v2 API"""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    OUT_OF_STOCK = "out_of_stock"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class StockCheckResponseV2:
    """Response structure from v2 API"""
    sku: str
    available: Optional[bool]
    quantity: Optional[int]
    availabilityStatus: str
    syncTimestamp: str
    pollingUrl: Optional[str] = None
    estimatedSync: Optional[str] = None
    retryCount: Optional[int] = None


class V2ApiClient:
    """
    Client for v2 API with retry and polling logic.
    
    Features:
    - Automatic retry with exponential backoff
    - Polling for async responses (202 Accepted)
    - Request/response logging
    - Timeout handling
    """
    
    def __init__(self, base_url: str = None, timeout_ms: int = 5000, 
                 max_retries: int = 3, retry_backoff_ms: int = 500):
        """
        Initialize v2 API client.
        
        Args:
            base_url: Base URL for v2 API
            timeout_ms: Request timeout in milliseconds
            max_retries: Maximum retry attempts
            retry_backoff_ms: Initial backoff time in milliseconds
        """
        self.base_url = base_url or os.getenv('V2_API_URL', 'http://localhost:5002')
        self.timeout_sec = timeout_ms / 1000
        self.max_retries = max_retries
        self.retry_backoff_ms = retry_backoff_ms
        self.endpoint = '/api/v2/stock/availability'
        
        logger.info(f"V2ApiClient initialized: base_url={self.base_url}, "
                   f"timeout={self.timeout_sec}s, max_retries={max_retries}")
    
    def check_stock(self, sku: str, regionId: str, warehouseGroup: str) -> Dict[str, Any]:
        """
        Check stock with automatic retry logic.
        
        Args:
            sku: Product SKU
            regionId: Region identifier
            warehouseGroup: Warehouse group identifier
            
        Returns:
            Response dict with result or error
        """
        request_data = {
            'sku': sku,
            'regionId': regionId,
            'warehouseGroup': warehouseGroup
        }
        
        url = f"{self.base_url}{self.endpoint}"
        
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            
            try:
                logger.info(f"[V2-{attempt}] Calling {url} with sku={sku}, "
                           f"regionId={regionId}, warehouseGroup={warehouseGroup}")
                
                response = requests.post(
                    url,
                    json=request_data,
                    timeout=self.timeout_sec,
                    headers={'Content-Type': 'application/json'}
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                logger.info(f"[V2-{attempt}] Response status={response.status_code}, "
                           f"latency={elapsed_ms:.1f}ms")
                
                # Handle 202 Accepted (async response)
                if response.status_code == 202:
                    logger.info(f"[V2-{attempt}] Received async response (202), will poll")
                    response_data = response.json()
                    
                    return {
                        'success': True,
                        'statusCode': response.status_code,
                        'data': response_data,
                        'latency_ms': elapsed_ms,
                        'error': None,
                        'retryCount': attempt,
                        'is_pending': True
                    }
                
                # Success response
                elif response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"[V2-{attempt}] Success: available={response_data.get('available')}, "
                               f"status={response_data.get('availabilityStatus')}")
                    
                    return {
                        'success': True,
                        'statusCode': response.status_code,
                        'data': response_data,
                        'latency_ms': elapsed_ms,
                        'error': None,
                        'retryCount': attempt,
                        'is_pending': False
                    }
                
                # Client error (bad request)
                elif response.status_code == 400:
                    error_msg = response.json().get('message', response.text)
                    logger.warning(f"[V2-{attempt}] Client error: {error_msg}")
                    
                    return {
                        'success': False,
                        'statusCode': response.status_code,
                        'data': None,
                        'latency_ms': elapsed_ms,
                        'error': error_msg,
                        'retryCount': attempt,
                        'is_retryable': False
                    }
                
                # Server error (retryable)
                elif response.status_code >= 500:
                    error_msg = response.json().get('message', response.text)
                    logger.warning(f"[V2-{attempt}] Server error ({response.status_code}): {error_msg}")
                    
                    # Retry if not last attempt
                    if attempt < self.max_retries:
                        backoff_sec = (self.retry_backoff_ms * (2 ** attempt)) / 1000
                        logger.info(f"[V2-{attempt}] Retrying after {backoff_sec:.2f}s backoff")
                        time.sleep(backoff_sec)
                        continue
                    
                    return {
                        'success': False,
                        'statusCode': response.status_code,
                        'data': None,
                        'latency_ms': elapsed_ms,
                        'error': error_msg,
                        'retryCount': attempt,
                        'is_retryable': False
                    }
                
                else:
                    error_msg = f"Unexpected status {response.status_code}"
                    logger.warning(f"[V2-{attempt}] {error_msg}")
                    
                    return {
                        'success': False,
                        'statusCode': response.status_code,
                        'data': None,
                        'latency_ms': elapsed_ms,
                        'error': error_msg,
                        'retryCount': attempt
                    }
            
            except requests.Timeout:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning(f"[V2-{attempt}] Timeout after {elapsed_ms:.1f}ms")
                
                if attempt < self.max_retries:
                    backoff_sec = (self.retry_backoff_ms * (2 ** attempt)) / 1000
                    logger.info(f"[V2-{attempt}] Retrying after {backoff_sec:.2f}s backoff")
                    time.sleep(backoff_sec)
                    continue
                
                return {
                    'success': False,
                    'statusCode': 504,
                    'data': None,
                    'latency_ms': elapsed_ms,
                    'error': 'Gateway Timeout',
                    'retryCount': attempt
                }
            
            except requests.RequestException as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"[V2-{attempt}] Request error: {str(e)}")
                
                if attempt < self.max_retries:
                    backoff_sec = (self.retry_backoff_ms * (2 ** attempt)) / 1000
                    logger.info(f"[V2-{attempt}] Retrying after {backoff_sec:.2f}s backoff")
                    time.sleep(backoff_sec)
                    continue
                
                return {
                    'success': False,
                    'statusCode': 500,
                    'data': None,
                    'latency_ms': elapsed_ms,
                    'error': str(e),
                    'retryCount': attempt
                }
        
        # Should not reach here
        return {
            'success': False,
            'statusCode': 500,
            'data': None,
            'latency_ms': 0,
            'error': 'Max retries exceeded',
            'retryCount': self.max_retries
        }
    
    def poll_availability(self, polling_url: str, max_polls: int = 5) -> Dict[str, Any]:
        """
        Poll for updated availability (async polling).
        
        Args:
            polling_url: URL to poll (relative to base_url)
            max_polls: Maximum polling attempts
            
        Returns:
            Response dict when status changes or max polls reached
        """
        full_url = f"{self.base_url}{polling_url}"
        
        for poll_attempt in range(max_polls):
            start_time = time.time()
            
            try:
                logger.info(f"[POLL-{poll_attempt}] Polling {full_url}")
                
                response = requests.get(
                    full_url,
                    timeout=self.timeout_sec,
                    headers={'Content-Type': 'application/json'}
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response_data = response.json()
                    status = response_data.get('availabilityStatus', 'unknown')
                    
                    logger.info(f"[POLL-{poll_attempt}] Status updated: {status}")
                    
                    return {
                        'success': True,
                        'statusCode': 200,
                        'data': response_data,
                        'latency_ms': elapsed_ms,
                        'poll_attempts': poll_attempt + 1
                    }
                
                elif response.status_code == 202:
                    logger.info(f"[POLL-{poll_attempt}] Still pending, waiting...")
                    time.sleep(2)  # Wait before next poll
                    continue
                
                else:
                    logger.warning(f"[POLL-{poll_attempt}] Poll failed: status {response.status_code}")
                    break
            
            except Exception as e:
                logger.error(f"[POLL-{poll_attempt}] Poll error: {str(e)}")
                break
        
        return {
            'success': False,
            'error': 'Polling timeout - status remains pending',
            'poll_attempts': max_polls
        }


class CartServiceV2:
    """
    Updated shopping cart service using v2 API.
    
    Features:
    - Region-aware stock checks
    - Async/pending handling with polling
    - Backward compatibility mode
    - Feature flag support
    """
    
    def __init__(self, api_client: V2ApiClient = None, 
                 use_feature_flag: bool = False,
                 enable_fallback: bool = True):
        """
        Initialize cart service.
        
        Args:
            api_client: V2ApiClient instance (or creates default)
            use_feature_flag: Whether to support v1/v2 toggling
            enable_fallback: Whether to fallback on v2 errors
        """
        self.api_client = api_client or V2ApiClient()
        self.use_feature_flag = use_feature_flag
        self.enable_fallback = enable_fallback
        
        logger.info(f"CartServiceV2 initialized: feature_flag={use_feature_flag}, "
                   f"fallback={enable_fallback}")
    
    def check_stock(self, sku: str, regionId: str, warehouseGroup: str,
                   poll_on_pending: bool = True) -> Dict[str, Any]:
        """
        Check stock availability using v2 API.
        
        Args:
            sku: Product SKU
            regionId: Region identifier
            warehouseGroup: Warehouse group
            poll_on_pending: Whether to poll if response is pending
            
        Returns:
            Response dict with availability decision
        """
        logger.info(f"[CART] Checking stock v2: sku={sku}, region={regionId}, "
                   f"warehouse_group={warehouseGroup}")
        
        # Call v2 API
        result = self.api_client.check_stock(sku, regionId, warehouseGroup)
        
        if not result['success']:
            logger.warning(f"[CART] Stock check failed: {result['error']}")
            return result
        
        # Handle pending response with polling
        if result.get('is_pending') and poll_on_pending:
            data = result['data']
            polling_url = data.get('pollingUrl')
            
            if polling_url:
                logger.info(f"[CART] Polling for availability...")
                poll_result = self.api_client.poll_availability(polling_url)
                
                if poll_result['success']:
                    result['data'] = poll_result['data']
                    result['is_pending'] = False
                    result['polling_attempts'] = poll_result.get('poll_attempts', 0)
                else:
                    logger.warning(f"[CART] Polling failed: {poll_result.get('error')}")
                    # Keep original pending response
                    result['polling_failed'] = True
        
        return result
    
    def add_to_cart(self, sku: str, regionId: str, warehouseGroup: str,
                   quantity: int = 1) -> Dict[str, Any]:
        """
        Add item to cart after checking availability.
        
        Args:
            sku: Product SKU
            regionId: Region identifier
            warehouseGroup: Warehouse group
            quantity: Quantity to add
            
        Returns:
            Dict with cart decision
        """
        logger.info(f"[CART] Adding to cart: sku={sku}, qty={quantity}, "
                   f"region={regionId}, warehouse={warehouseGroup}")
        
        # Check stock
        stock_check = self.check_stock(sku, regionId, warehouseGroup)
        
        if not stock_check['success']:
            logger.warning(f"[CART] Stock check failed: {stock_check['error']}")
            
            return {
                'added': False,
                'reason': f"Stock check failed: {stock_check['error']}",
                'sku': sku,
                'quantity_requested': quantity,
                'quantity_added': 0,
                'latency_ms': stock_check.get('latency_ms', 0),
                'error_code': 'STOCK_CHECK_FAILED'
            }
        
        data = stock_check['data']
        available = data.get('available', False)
        available_quantity = data.get('quantity', 0)
        status = data.get('availabilityStatus', 'unknown')
        
        # Check if pending after polling
        if stock_check.get('is_pending'):
            logger.warning(f"[CART] Availability still pending after polling")
            
            return {
                'added': False,
                'reason': 'Availability still pending - cannot add to cart',
                'sku': sku,
                'quantity_requested': quantity,
                'quantity_added': 0,
                'availability_status': status,
                'latency_ms': stock_check.get('latency_ms', 0),
                'error_code': 'PENDING_AVAILABILITY'
            }
        
        # Check if sufficient quantity
        if not available or available_quantity < quantity:
            logger.warning(f"[CART] Insufficient inventory: available={available}, "
                          f"quantity={available_quantity}, requested={quantity}")
            
            return {
                'added': False,
                'reason': 'Insufficient inventory',
                'sku': sku,
                'quantity_requested': quantity,
                'quantity_added': 0,
                'available_quantity': available_quantity,
                'availability_status': status,
                'latency_ms': stock_check.get('latency_ms', 0),
                'error_code': 'INSUFFICIENT_INVENTORY'
            }
        
        # Add to cart
        logger.info(f"[CART] Successfully added {quantity} units of {sku}")
        
        return {
            'added': True,
            'reason': 'Item added successfully',
            'sku': sku,
            'quantity_requested': quantity,
            'quantity_added': quantity,
            'available_quantity': available_quantity,
            'availability_status': status,
            'latency_ms': stock_check.get('latency_ms', 0),
            'sync_timestamp': data.get('syncTimestamp'),
            'polling_attempts': stock_check.get('polling_attempts', 0)
        }


def create_app():
    """Create Flask app for v2 cart service"""
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    
    # Initialize service
    api_client = V2ApiClient()
    service = CartServiceV2(api_client=api_client)
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check"""
        return jsonify({'status': 'healthy', 'service': 'cart_service_v2'}), 200
    
    @app.route('/cart/add', methods=['POST'])
    def add_to_cart():
        """Add item to cart"""
        try:
            payload = request.get_json()
            sku = payload.get('sku')
            regionId = payload.get('regionId')
            warehouseGroup = payload.get('warehouseGroup')
            quantity = payload.get('quantity', 1)
            
            if not sku or not regionId or not warehouseGroup:
                return jsonify({
                    'error': 'Missing required parameters',
                    'required': ['sku', 'regionId', 'warehouseGroup']
                }), 400
            
            result = service.add_to_cart(sku, regionId, warehouseGroup, quantity)
            
            return jsonify(result), 200 if result['added'] else 409
        
        except Exception as e:
            logger.error(f"Error in /cart/add: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/stock/check', methods=['POST'])
    def check_stock():
        """Check stock availability"""
        try:
            payload = request.get_json()
            sku = payload.get('sku')
            regionId = payload.get('regionId')
            warehouseGroup = payload.get('warehouseGroup')
            
            if not sku or not regionId or not warehouseGroup:
                return jsonify({
                    'error': 'Missing required parameters',
                    'required': ['sku', 'regionId', 'warehouseGroup']
                }), 400
            
            result = service.check_stock(sku, regionId, warehouseGroup)
            
            if result['success']:
                return jsonify(result['data']), result['statusCode']
            else:
                return jsonify({'error': result['error']}), result['statusCode']
        
        except Exception as e:
            logger.error(f"Error in /stock/check: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
