from flask import Blueprint, jsonify, request
try:
    from ..db import get_db_connection, get_sharded_db_layer
    from ..auth import token_required
    from ..logger import log_action
except ImportError:
    from db import get_db_connection, get_sharded_db_layer
    from auth import token_required
    from logger import log_action

member_bp = Blueprint('member', __name__)


@member_bp.route('/portfolio/<int:id>', methods=['GET'])
@token_required
def get_portfolio(id):
    # RBAC Check: Regular users can only see their own portfolio
    if request.user['role'] != 'admin' and request.user['member_id'] != id:
        log_action(request.user['username'], f"UNAUTHORIZED ACCESS ATTEMPT: Portfolio {id}")
        return jsonify({"error": "Access denied"}), 403

    sharded_db = get_sharded_db_layer()
    member = sharded_db.get_member_by_id(id)

    if not member:
        return jsonify({"error": "Member not found"}), 404

    return jsonify({"member": member}), 200
