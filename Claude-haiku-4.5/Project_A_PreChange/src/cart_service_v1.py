"""
Project A - Pre-Change: Legacy Cart Service using v1 API

This module implements a shopping cart service that calls the legacy
/api/v1/checkStock endpoint to determine product availability.

Key characteristics:
- Simple, synchronous API call
- Expects basic request: {sku, warehouseId}
- Returns direct availability: {available, quantity, lastUpdated}
"""

import os
import requests
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
try:
    log_path = Path(__file__).parent.parent / 'logs' / 'log_pre.txt'
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


@dataclass
class StockCheckRequest:
    """Request structure for v1 API"""
    sku: str
    warehouseId: str


@dataclass
class StockCheckResponse:
    """Response structure from v1 API"""
    sku: str
    available: Optional[bool]
    quantity: Optional[int]
    lastUpdated: str


class CartServiceV1:
    """
    Shopping cart service using legacy v1 API.
    
    Responsibilities:
    - Call /api/v1/checkStock for inventory verification
    - Handle availability decisions
    - Log request/response cycles
    - Track performance metrics
    """
    
    def __init__(self, api_base_url: str = None, timeout_ms: int = 5000):
        """
        Initialize cart service.
        
        Args:
            api_base_url: Base URL for v1 API (default from env or http://localhost:5001)
            timeout_ms: Request timeout in milliseconds
        """
        self.api_base_url = api_base_url or os.getenv('V1_API_URL', 'http://localhost:5001')
        self.timeout_sec = timeout_ms / 1000
        self.endpoint = '/api/v1/checkStock'
        logger.info(f"CartServiceV1 initialized with base_url={self.api_base_url}, timeout={self.timeout_sec}s")
    
    def check_stock(self, sku: str, warehouseId: str) -> Dict[str, Any]:
        """
        Check stock availability using v1 API.
        
        Args:
            sku: Product SKU
            warehouseId: Warehouse identifier
            
        Returns:
            Dict containing availability result and metadata
            
        Raises:
            RequestException: Network or API error
        """
        request_data = {
            'sku': sku,
            'warehouseId': warehouseId
        }
        
        url = f"{self.api_base_url}{self.endpoint}"
        start_time = time.time()
        
        try:
            logger.info(f"[V1] Calling {url} with sku={sku}, warehouseId={warehouseId}")
            
            response = requests.post(
                url,
                json=request_data,
                timeout=self.timeout_sec,
                headers={'Content-Type': 'application/json'}
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            logger.info(f"[V1] Response status={response.status_code}, latency={elapsed_ms:.1f}ms")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"[V1] Success: available={response_data.get('available')}, "
                           f"quantity={response_data.get('quantity')}")
                
                return {
                    'success': True,
                    'statusCode': response.status_code,
                    'data': response_data,
                    'latency_ms': elapsed_ms,
                    'error': None,
                    'retryCount': 0
                }
            else:
                error_msg = response.text or 'Unknown error'
                logger.warning(f"[V1] API returned status {response.status_code}: {error_msg}")
                
                return {
                    'success': False,
                    'statusCode': response.status_code,
                    'data': None,
                    'latency_ms': elapsed_ms,
                    'error': error_msg,
                    'retryCount': 0
                }
        
        except requests.Timeout:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"[V1] Request timeout after {elapsed_ms:.1f}ms")
            
            return {
                'success': False,
                'statusCode': 504,
                'data': None,
                'latency_ms': elapsed_ms,
                'error': 'Gateway Timeout',
                'retryCount': 0
            }
        
        except requests.RequestException as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"[V1] Request failed: {str(e)}", exc_info=True)
            
            return {
                'success': False,
                'statusCode': 500,
                'data': None,
                'latency_ms': elapsed_ms,
                'error': str(e),
                'retryCount': 0
            }
    
    def add_to_cart(self, sku: str, warehouseId: str, quantity: int = 1) -> Dict[str, Any]:
        """
        Add item to cart after checking availability.
        
        Args:
            sku: Product SKU
            warehouseId: Warehouse identifier
            quantity: Quantity to add (default 1)
            
        Returns:
            Dict with cart decision (added/failed) and reason
        """
        logger.info(f"[CART] Adding to cart: sku={sku}, qty={quantity}")
        
        # Check stock first
        stock_check = self.check_stock(sku, warehouseId)
        
        if not stock_check['success']:
            logger.warning(f"[CART] Stock check failed: {stock_check['error']}")
            return {
                'added': False,
                'reason': f"Stock check failed: {stock_check['error']}",
                'sku': sku,
                'quantity_requested': quantity,
                'quantity_added': 0,
                'latency_ms': stock_check['latency_ms']
            }
        
        data = stock_check['data']
        available = data.get('available', False)
        available_quantity = data.get('quantity', 0)
        
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
                'latency_ms': stock_check['latency_ms']
            }
        
        # Simulate adding to cart (in real app, would update cart storage)
        logger.info(f"[CART] Successfully added {quantity} units of {sku}")
        
        return {
            'added': True,
            'reason': 'Item added successfully',
            'sku': sku,
            'quantity_requested': quantity,
            'quantity_added': quantity,
            'available_quantity': available_quantity,
            'latency_ms': stock_check['latency_ms']
        }


def create_app():
    """
    Create Flask app that exposes cart service endpoints.
    Used for integration testing.
    """
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    service = CartServiceV1()
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'service': 'cart_service_v1'}), 200
    
    @app.route('/cart/add', methods=['POST'])
    def add_to_cart():
        """Add item to cart"""
        try:
            payload = request.get_json()
            sku = payload.get('sku')
            warehouseId = payload.get('warehouseId')
            quantity = payload.get('quantity', 1)
            
            if not sku or not warehouseId:
                return jsonify({'error': 'Missing sku or warehouseId'}), 400
            
            result = service.add_to_cart(sku, warehouseId, quantity)
            
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
            warehouseId = payload.get('warehouseId')
            
            if not sku or not warehouseId:
                return jsonify({'error': 'Missing sku or warehouseId'}), 400
            
            result = service.check_stock(sku, warehouseId)
            
            if result['success']:
                return jsonify(result['data']), result['statusCode']
            else:
                return jsonify({'error': result['error']}), result['statusCode']
        
        except Exception as e:
            logger.error(f"Error in /stock/check: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    return app


if __name__ == '__main__':
    # For standalone testing
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
