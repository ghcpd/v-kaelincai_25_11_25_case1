"""
Mock server for v2 API (/api/v2/stock/availability)

Simulates new inventory API with:
- Region-aware parameters
- Async responses (202 Accepted)
- Polling support for eventual consistency
- Configurable delays and errors
"""

import os
import json
import logging
import time
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from threading import Timer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockAPIv2:
    """Mock v2 API server"""
    
    def __init__(self):
        """Initialize with mock inventory data"""
        self.inventory = {
            'ABC123': {
                'regionId': 'ap-sg-1',
                'warehouseGroup': 'WG-2',
                'quantity': 45,
                'available': True,
                'status': 'confirmed'
            },
            'XYZ789': {
                'regionId': 'us-west-2',
                'warehouseGroup': 'WG-1',
                'quantity': 0,
                'available': False,
                'status': 'out_of_stock'
            },
            'NEW456': {
                'regionId': 'eu-central-1',
                'warehouseGroup': 'WG-3',
                'quantity': None,
                'available': None,
                'status': 'pending',
                'async_delay': 10  # Seconds until confirmed
            },
            'DEF012': {
                'regionId': 'ap-remote-1',
                'warehouseGroup': 'WG-4',
                'quantity': 15,
                'available': True,
                'status': 'confirmed'
            },
            'SLOW001': {
                'regionId': 'ap-remote-1',
                'warehouseGroup': 'WG-5',
                'quantity': 8,
                'available': True,
                'status': 'confirmed',
                'delay': 5.0  # Seconds delay before response
            },
            'TOGGLE001': {
                'regionId': 'test-region-1',
                'warehouseGroup': 'WG-TEST',
                'quantity': 30,
                'available': True,
                'status': 'confirmed'
            }
        }
        
        self.call_count = {}
        self.pending_status = {}  # Track pending items for polling
        self.init_pending_items()
    
    def init_pending_items(self):
        """Initialize pending items that will become confirmed"""
        for sku, item in self.inventory.items():
            if item['status'] == 'pending':
                # Schedule status change
                async_delay = item.get('async_delay', 10)
                logger.info(f"[MOCK v2] Scheduling {sku} to become confirmed in {async_delay}s")
                self.pending_status[sku] = {
                    'created_at': time.time(),
                    'delay': async_delay,
                    'confirmed_data': {
                        'quantity': 23,
                        'available': True,
                        'status': 'confirmed'
                    }
                }
    
    def check_stock(self, sku: str, regionId: str, warehouseGroup: str) -> dict:
        """
        Mock inventory check with async support.
        
        Args:
            sku: Product SKU
            regionId: Region ID
            warehouseGroup: Warehouse group
            
        Returns:
            Response dict with status and data
        """
        logger.info(f"[MOCK v2] Received checkStock: sku={sku}, regionId={regionId}, "
                   f"warehouseGroup={warehouseGroup}")
        
        # Track calls
        self.call_count[sku] = self.call_count.get(sku, 0) + 1
        
        if sku not in self.inventory:
            logger.warning(f"[MOCK v2] SKU not found: {sku}")
            return {
                'statusCode': 404,
                'error': 'Product not found'
            }
        
        item = self.inventory[sku]
        
        # Simulate delay if configured
        if 'delay' in item:
            logger.info(f"[MOCK v2] Simulating delay of {item['delay']}s for {sku}")
            time.sleep(item['delay'])
        
        # Check for pending items that should now be confirmed
        if sku in self.pending_status:
            pending_info = self.pending_status[sku]
            elapsed = time.time() - pending_info['created_at']
            
            if elapsed >= pending_info['delay']:
                # Status has been confirmed
                logger.info(f"[MOCK v2] {sku} is now confirmed after {elapsed:.1f}s")
                
                response = {
                    'statusCode': 200,
                    'body': {
                        'sku': sku,
                        'available': pending_info['confirmed_data']['available'],
                        'quantity': pending_info['confirmed_data']['quantity'],
                        'availabilityStatus': 'confirmed',
                        'syncTimestamp': datetime.utcnow().isoformat() + 'Z'
                    }
                }
                
                # Clean up pending
                del self.pending_status[sku]
                
                logger.info(f"[MOCK v2] Response: {response['body']}")
                return response
        
        # For pending items, return 202 with polling URL
        if item['status'] == 'pending':
            response = {
                'statusCode': 202,
                'body': {
                    'sku': sku,
                    'available': None,
                    'quantity': None,
                    'availabilityStatus': 'pending',
                    'syncTimestamp': datetime.utcnow().isoformat() + 'Z',
                    'estimatedSync': (datetime.utcnow() + timedelta(seconds=10)).isoformat() + 'Z',
                    'pollingUrl': f'/api/v2/stock/{sku}?regionId={regionId}&warehouseGroup={warehouseGroup}'
                }
            }
            
            logger.info(f"[MOCK v2] Response (async): {response['body']}")
            return response
        
        # Normal confirmed response
        response = {
            'statusCode': 200,
            'body': {
                'sku': sku,
                'available': item['available'],
                'quantity': item['quantity'],
                'availabilityStatus': item['status'],
                'syncTimestamp': (datetime.utcnow() - timedelta(minutes=5)).isoformat() + 'Z'
            }
        }
        
        logger.info(f"[MOCK v2] Response: {response['body']}")
        return response


def create_mock_app():
    """Create Flask app for mock v2 API"""
    app = Flask(__name__)
    mock = MockAPIv2()
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check"""
        return jsonify({'status': 'healthy', 'service': 'mock_api_v2'}), 200
    
    @app.route('/api/v2/stock/availability', methods=['POST'])
    def check_stock():
        """Mock v2 checkStock endpoint"""
        try:
            payload = request.get_json()
            sku = payload.get('sku')
            regionId = payload.get('regionId')
            warehouseGroup = payload.get('warehouseGroup')
            
            if not sku or not regionId or not warehouseGroup:
                logger.warning("[MOCK v2] Missing required parameters")
                return jsonify({
                    'error': 'Bad Request',
                    'message': 'Missing required parameters: sku, regionId, warehouseGroup'
                }), 400
            
            result = mock.check_stock(sku, regionId, warehouseGroup)
            
            if 'error' in result:
                return jsonify({'error': result['error']}), result['statusCode']
            else:
                return jsonify(result['body']), result['statusCode']
        
        except Exception as e:
            logger.error(f"[MOCK v2] Error: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/v2/stock/<sku>', methods=['GET'])
    def poll_stock(sku):
        """Poll endpoint for async updates"""
        try:
            regionId = request.args.get('regionId')
            warehouseGroup = request.args.get('warehouseGroup')
            
            logger.info(f"[MOCK v2] Poll request for {sku}")
            
            result = mock.check_stock(sku, regionId, warehouseGroup)
            
            if 'error' in result:
                return jsonify({'error': result['error']}), result['statusCode']
            else:
                return jsonify(result['body']), result['statusCode']
        
        except Exception as e:
            logger.error(f"[MOCK v2] Poll error: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/stats', methods=['GET'])
    def stats():
        """Return call statistics"""
        return jsonify({
            'call_count': mock.call_count,
            'total_calls': sum(mock.call_count.values()),
            'pending_items': list(mock.pending_status.keys())
        }), 200
    
    return app


if __name__ == '__main__':
    app = create_mock_app()
    port = int(os.getenv('MOCK_V2_PORT', 5002))
    logger.info(f"Starting Mock API v2 on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
