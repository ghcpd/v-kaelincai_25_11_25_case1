"""
Mock API v2 Server
Simulates /api/v2/stock/availability endpoint
Supports region-aware, async/pending responses
"""
from flask import Flask, request, jsonify
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stock database (simulated) with region awareness
STOCK_DB = {
    "ABC123": {
        "ap-sg-1": {"WG-2": {"available": True, "quantity": 12, "status": "confirmed"}},
        "us-east-1": {"WG-1": {"available": True, "quantity": 8, "status": "confirmed"}}
    },
    "XYZ789": {
        "us-east-1": {"WG-1": {"available": False, "quantity": 0, "status": "confirmed"}},
        "ap-sg-1": {"WG-2": {"available": False, "quantity": 0, "status": "confirmed"}}
    },
    "DEF456": {
        "eu-west-1": {"WG-3": {"available": True, "quantity": 15, "status": "pending"}}
    },
    "GHI999": {
        "us-east-1": {"WG-1": {"available": True, "quantity": 8, "status": "confirmed"}}
    },
    "JKL111": {
        "ap-ne-1": {"WG-5": {"available": True, "quantity": 5, "status": "confirmed"}}
    },
    "MNO222": {
        "us-west-2": {"WG-2": {"available": True, "quantity": 3, "status": "confirmed"}}
    }
}


@app.route('/api/v2/stock/availability', methods=['POST'])
def check_availability():
    """
    New v2 stock availability endpoint
    
    Request: {
        "sku": "ABC123",
        "regionId": "ap-sg-1",
        "warehouseGroup": "WG-2",
        "quantity": 5
    }
    Response: {
        "sku": "ABC123",
        "available": true,
        "quantity": 12,
        "availabilityStatus": "confirmed",
        "syncTimestamp": "2025-11-25T12:00:00Z",
        "regionId": "ap-sg-1",
        "warehouseGroup": "WG-2"
    }
    """
    data = request.get_json()
    
    # Validate required parameters
    if not data:
        return jsonify({
            "error": "Request body required",
            "code": "INVALID_REQUEST"
        }), 400
    
    sku = data.get('sku')
    region_id = data.get('regionId')
    warehouse_group = data.get('warehouseGroup')
    requested_quantity = data.get('quantity', 1)
    
    if not sku:
        return jsonify({
            "error": "Missing required parameter: sku",
            "code": "INVALID_REQUEST"
        }), 400
    
    if not region_id:
        return jsonify({
            "error": "Missing required parameter: regionId",
            "code": "INVALID_REQUEST"
        }), 400
    
    if not warehouse_group:
        return jsonify({
            "error": "Missing required parameter: warehouseGroup",
            "code": "INVALID_REQUEST"
        }), 400
    
    # Simulate error for JKL111 (TC005)
    if sku == "JKL111":
        logger.error(f"Simulating server error for SKU: {sku}")
        return jsonify({
            "error": "Internal server error",
            "code": "SERVER_ERROR"
        }), 500
    
    # Retrieve stock info
    sku_data = STOCK_DB.get(sku)
    
    if not sku_data:
        return jsonify({
            "error": "SKU not found",
            "code": "NOT_FOUND",
            "sku": sku
        }), 404
    
    region_data = sku_data.get(region_id)
    
    if not region_data:
        return jsonify({
            "error": f"Region {region_id} not available for SKU {sku}",
            "code": "REGION_NOT_FOUND",
            "sku": sku,
            "regionId": region_id
        }), 404
    
    warehouse_data = region_data.get(warehouse_group)
    
    if not warehouse_data:
        return jsonify({
            "error": f"Warehouse group {warehouse_group} not found in region {region_id}",
            "code": "WAREHOUSE_NOT_FOUND",
            "sku": sku,
            "regionId": region_id,
            "warehouseGroup": warehouse_group
        }), 404
    
    # Build response
    available = warehouse_data["available"]
    quantity = warehouse_data["quantity"]
    status = warehouse_data["status"]
    
    sync_time = datetime.utcnow()
    
    response = {
        "sku": sku,
        "available": available,
        "quantity": quantity,
        "availabilityStatus": status,
        "syncTimestamp": sync_time.isoformat() + "Z",
        "regionId": region_id,
        "warehouseGroup": warehouse_group
    }
    
    # Add async fields for pending status
    if status == "pending":
        response["estimatedSyncTime"] = 5  # seconds
        response["syncTimestamp"] = (sync_time + timedelta(seconds=5)).isoformat() + "Z"
    
    # Mark if at threshold (e.g., quantity == 3)
    if quantity == 3:
        response["atThreshold"] = True
    
    logger.info(f"v2 API response for {sku}/{region_id}/{warehouse_group}: {response}")
    return jsonify(response), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "version": "v2"}), 200


if __name__ == '__main__':
    logger.info("Starting Mock API v2 server on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)
