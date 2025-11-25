"""
Mock server for v1 API (/api/v1/checkStock)

Simulates legacy inventory API with configurable behaviors:
- Normal immediate responses
- Timeouts
- Various error conditions
"""

import os
import json
import logging
import time
from flask import Flask, request, jsonify
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockAPIv1:
    """Mock v1 API server"""
    
    def __init__(self):
        """Initialize with mock inventory data"""
        self.inventory = {
            'ABC123': {'warehouseId': 'WH-US-EAST-1', 'quantity': 45, 'available': True},
            'XYZ789': {'warehouseId': 'WH-US-WEST-2', 'quantity': 0, 'available': False},
            'NEW456': {'warehouseId': 'WH-EU-CENTRAL-1', 'quantity': None, 'available': None},
            'DEF012': {'warehouseId': 'WH-APAC-1', 'quantity': 15, 'available': True},
            'SLOW001': {'warehouseId': 'WH-REMOTE-1', 'quantity': 8, 'available': True, 'delay': 5.0},
            'TOGGLE001': {'warehouseId': 'WH-TEST-1', 'quantity': 30, 'available': True},
        }
        self.call_count = {}
    
    def check_stock(self, sku: str, warehouseId: str) -> dict:
        """
        Mock inventory check.
        
        Args:
            sku: Product SKU
            warehouseId: Warehouse ID (used to validate request)
            
        Returns:
            Response dict with status and data
        """
        logger.info(f"[MOCK v1] Received checkStock: sku={sku}, warehouseId={warehouseId}")
        
        # Track calls
        self.call_count[sku] = self.call_count.get(sku, 0) + 1
        
        if sku not in self.inventory:
            logger.warning(f"[MOCK v1] SKU not found: {sku}")
            return {
                'statusCode': 404,
                'error': 'Product not found'
            }
        
        item = self.inventory[sku]
        
        # Simulate delay if configured
        if 'delay' in item:
            logger.info(f"[MOCK v1] Simulating delay of {item['delay']}s for {sku}")
            time.sleep(item['delay'])
        
        response = {
            'statusCode': 200,
            'body': {
                'sku': sku,
                'available': item['available'],
                'quantity': item['quantity'],
                'lastUpdated': (datetime.utcnow() - timedelta(minutes=5)).isoformat() + 'Z'
            }
        }
        
        logger.info(f"[MOCK v1] Response: {response['body']}")
        return response


def create_mock_app():
    """Create Flask app for mock v1 API"""
    app = Flask(__name__)
    mock = MockAPIv1()
    
    @app.route('/health', methods=['GET'])
    def health():
        """Health check"""
        return jsonify({'status': 'healthy', 'service': 'mock_api_v1'}), 200
    
    @app.route('/api/v1/checkStock', methods=['POST'])
    def check_stock():
        """Mock v1 checkStock endpoint"""
        try:
            payload = request.get_json()
            sku = payload.get('sku')
            warehouseId = payload.get('warehouseId')
            
            if not sku or not warehouseId:
                logger.warning("[MOCK v1] Missing required parameters")
                return jsonify({'error': 'Missing sku or warehouseId'}), 400
            
            result = mock.check_stock(sku, warehouseId)
            
            if result['statusCode'] == 200:
                return jsonify(result['body']), 200
            else:
                return jsonify({'error': result.get('error')}), result['statusCode']
        
        except Exception as e:
            logger.error(f"[MOCK v1] Error: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @app.route('/stats', methods=['GET'])
    def stats():
        """Return call statistics"""
        return jsonify({
            'call_count': mock.call_count,
            'total_calls': sum(mock.call_count.values())
        }), 200
    
    return app


if __name__ == '__main__':
    app = create_mock_app()
    port = int(os.getenv('MOCK_V1_PORT', 5001))
    logger.info(f"Starting Mock API v1 on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
