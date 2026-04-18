import datetime
from flask import Blueprint, jsonify, request
try:
    from ..db import get_db_connection, get_sharded_db_layer
    from ..auth import token_required
    from ..logger import log_action
except ImportError:
    from db import get_db_connection, get_sharded_db_layer
    from auth import token_required
    from logger import log_action

patient_bp = Blueprint('patient', __name__)


def _serialize_time_rows(rows, date_keys=None, time_keys=None):
    date_keys = date_keys or []
    time_keys = time_keys or []
    for row in rows:
        for key in date_keys:
            if row.get(key) and hasattr(row[key], 'isoformat'):
                row[key] = row[key].isoformat()
        for key in time_keys:
            if row.get(key) and hasattr(row[key], 'seconds'):
                total = row[key].seconds
                row[key] = f"{total//3600:02d}:{(total%3600)//60:02d}"


@patient_bp.route('/doctors', methods=['GET'])
@token_required
def get_doctors():
    sharded_db = get_sharded_db_layer()
    doctors = sharded_db.get_all_doctors()
    return jsonify({"doctors": doctors}), 200


@patient_bp.route('/slots/<int:doctor_id>', methods=['GET'])
@token_required
def get_slots(doctor_id):
    # For sharded architecture, return empty slots
    # In production, would query sharded slots table
    return jsonify({"slots": []}), 200


@patient_bp.route('/doctor/slots', methods=['GET'])
@token_required
def get_my_doctor_slots():
    if request.user.get('member_type') != 'Doctor':
        log_action(request.user['username'], "UNAUTHORIZED ACCESS ATTEMPT: Doctor slots")
        return jsonify({"error": "Access denied"}), 403

    # For sharded architecture, return empty slots
    return jsonify({"slots": []}), 200


@patient_bp.route('/doctor/appointments', methods=['GET'])
@token_required
def doctor_appointments():
    if request.user.get('member_type') != 'Doctor':
        log_action(request.user['username'], "UNAUTHORIZED ACCESS ATTEMPT: Doctor appointments")
        return jsonify({"error": "Access denied"}), 403

    selected_date = request.args.get('date') or datetime.date.today().isoformat()

    # For sharded architecture, return empty appointments
    return jsonify({"appointments": [], "date": selected_date}), 200


@patient_bp.route('/doctor/patients', methods=['GET'])
@token_required
def doctor_patients():
    if request.user.get('member_type') != 'Doctor':
        log_action(request.user['username'], "UNAUTHORIZED ACCESS ATTEMPT: Doctor patients")
        return jsonify({"error": "Access denied"}), 403

    # For sharded architecture, return empty patients list
    return jsonify({"patients": []}), 200


@patient_bp.route('/my_appointments', methods=['GET'])
@token_required
def my_appointments():
    # For sharded architecture, return empty appointments
    return jsonify({"appointments": []}), 200
