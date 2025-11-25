"""
Mock API v1 Server
Simulates /api/v1/checkStock endpoint
"""
from flask import Flask, request, jsonify
import logging
import json
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load test data for responses
TEST_DATA_PATH = "../data/test_data.json"

# Stock database (simulated)
STOCK_DB = {
    "ABC123": {"available": True, "stock": 12},
    "XYZ789": {"available": False, "stock": 0},
    "DEF456": {"available": True, "stock": 15},
    "GHI999": {"available": True, "stock": 8},
    "JKL111": {"available": True, "stock": 5},
    "MNO222": {"available": True, "stock": 3}
}


@app.route('/api/v1/checkStock', methods=['POST'])
def check_stock():
    """
    Legacy v1 stock check endpoint
    
    Request: {"sku": "ABC123"}
    Response: {"sku": "ABC123", "available": true, "stock": 12}
    """
    data = request.get_json()
    
    if not data or 'sku' not in data:
        return jsonify({
            "error": "Missing required parameter: sku",
            "code": "INVALID_REQUEST"
        }), 400
    
    sku = data['sku']
    
    # Simulate error for JKL111 (TC005)
    if sku == "JKL111":
        logger.error(f"Simulating server error for SKU: {sku}")
        return jsonify({
            "error": "Internal server error",
            "code": "SERVER_ERROR"
        }), 500
    
    # Retrieve stock info
    stock_info = STOCK_DB.get(sku)
    
    if stock_info is None:
        return jsonify({
            "error": "SKU not found",
            "code": "NOT_FOUND"
        }), 404
    
    response = {
        "sku": sku,
        "available": stock_info["available"],
        "stock": stock_info["stock"]
    }
    
    logger.info(f"v1 API response for {sku}: {response}")
    return jsonify(response), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "version": "v1"}), 200


if __name__ == '__main__':
    logger.info("Starting Mock API v1 server on port 5001")
    app.run(host='0.0.0.0', port=5001, debug=False)
