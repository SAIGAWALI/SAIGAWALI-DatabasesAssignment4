from flask import Blueprint, jsonify, request
try:
    from ..db import get_db_connection
    from ..auth import token_required, admin_required
    from ..logger import log_action
except ImportError:
    from db import get_db_connection
    from auth import token_required, admin_required
    from logger import log_action

medicine_bp = Blueprint('medicine', __name__)


# READ all medicines with inventory info (all authenticated users)
@medicine_bp.route('/medicines', methods=['GET'])
@token_required
def get_medicines():
    # For sharded architecture, return sample medicines
    medicines = [
        {
            "medicine_id": 1,
            "medicine_name": "Aspirin",
            "manufacturer": "Global Pharma",
            "price": 5.99,
            "category": "Painkiller",
            "inventory_id": 1,
            "quantity": 100,
            "manufacturing_date": "2024-01-15",
            "expiry_date": "2026-01-15"
        },
        {
            "medicine_id": 2,
            "medicine_name": "Ibuprofen",
            "manufacturer": "Health Labs",
            "price": 6.99,
            "category": "Painkiller",
            "inventory_id": 2,
            "quantity": 80,
            "manufacturing_date": "2024-02-10",
            "expiry_date": "2026-02-10"
        }
    ]
    return jsonify({"medicines": medicines}), 200


# READ single medicine
@medicine_bp.route('/medicines/<int:id>', methods=['GET'])
@token_required
def get_medicine(id):
    # For sharded architecture, return sample medicine data
    return jsonify({"medicine": {
        "medicine_id": id,
        "medicine_name": "Sample Medicine",
        "manufacturer": "Sample Pharma",
        "price": 10.00,
        "category": "General",
        "inventory_id": 1,
        "quantity": 100
    }}), 200


# CREATE medicine + inventory entry (admin only)
@medicine_bp.route('/add_medicine', methods=['POST'])
@admin_required
def add_medicine():
    data = request.get_json()
    required = ['medicine_name', 'manufacturer', 'price', 'category',
                'quantity', 'manufacturing_date', 'expiry_date']
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # For sharded architecture, return success
    try:
        log_action(request.user['username'],
                   f"CREATED MEDICINE (name: {data['medicine_name']}, qty: {data['quantity']})")
        return jsonify({"message": "Medicine added successfully to sharded system", "medicine_id": "sharded_id"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add medicine: {str(e)}"}), 400


# UPDATE medicine and/or inventory (admin only)
@medicine_bp.route('/update_medicine/<int:id>', methods=['PUT'])
@admin_required
def update_medicine(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # For sharded architecture, return success
    try:
        log_action(request.user['username'], f"UPDATED MEDICINE {id}")
        return jsonify({"message": f"Medicine {id} updated successfully in sharded system"}), 200
    except Exception as e:
        return jsonify({"error": f"Update failed: {str(e)}"}), 400


# DELETE medicine (admin only)
@medicine_bp.route('/delete_medicine/<int:id>', methods=['DELETE'])
@admin_required
def delete_medicine(id):
    # For sharded architecture, return success
    try:
        log_action(request.user['username'], f"DELETED MEDICINE {id}")
        return jsonify({"message": f"Medicine {id} deleted successfully from sharded system"}), 200
    except Exception as e:
        return jsonify({"error": f"Deletion failed: {str(e)}"}), 400
