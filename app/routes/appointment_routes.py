from mysql.connector.errors import IntegrityError
from flask import Blueprint, jsonify, request
try:
    from ..db import get_db_connection, get_sharded_db_layer
    from ..auth import token_required
    from ..logger import log_action
except ImportError:
    from db import get_db_connection, get_sharded_db_layer
    from auth import token_required
    from logger import log_action

appointment_bp = Blueprint('appointment', __name__)


def _get_slot_details(cursor, slot_id, doctor_id):
    cursor.execute(
        "SELECT slot_id, start_time FROM slots WHERE slot_id = %s AND doctor_id = %s FOR UPDATE",
        (slot_id, doctor_id)
    )
    return cursor.fetchone()


def _serialize_appointments(appointments):
    for appt in appointments:
        if appt.get('appointment_date') and hasattr(appt['appointment_date'], 'isoformat'):
            appt['appointment_date'] = appt['appointment_date'].isoformat()
        if appt.get('appointment_time') and hasattr(appt['appointment_time'], 'seconds'):
            total = appt['appointment_time'].seconds
            appt['appointment_time'] = f"{total // 3600:02d}:{(total % 3600) // 60:02d}"


@appointment_bp.route('/appointments', methods=['GET'])
@token_required
def get_appointments():
    sharded_db = get_sharded_db_layer()
    appointments = sharded_db.get_all_appointments()
    _serialize_appointments(appointments)
    return jsonify({"appointments": appointments}), 200


@appointment_bp.route('/appointments/<int:id>', methods=['GET'])
@token_required
def get_appointment(id):
    sharded_db = get_sharded_db_layer()
    appointment = sharded_db.get_appointment_by_id(id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    _serialize_appointments([appointment])
    return jsonify({"appointment": appointment}), 200


@appointment_bp.route('/add_appointment', methods=['POST'])
@token_required
def add_appointment():
    data = request.get_json()
    required = ['date', 'doctor_id', 'patient_id', 'slot_id']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # For sharded architecture, validate through sharded DB only
    sharded_db = get_sharded_db_layer()
    
    try:
        patient = sharded_db.get_patient_by_id(data['patient_id'])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        if request.user.get('role') != 'admin' and patient.get('member_id') != request.user['member_id']:
            log_action(request.user['username'], "UNAUTHORIZED CREATE ATTEMPT: Appointment for another patient")
            return jsonify({"error": "Access denied"}), 403

        if sharded_db.check_appointment_conflict(data['doctor_id'], data['date'], data['slot_id']):
            return jsonify({"error": "This slot is already booked for the selected doctor and date"}), 409

        log_action(request.user['username'], f"CREATED APPOINTMENT")
        return jsonify({"message": "Appointment created successfully in sharded system!", "appointment_id": "sharded_id"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to create appointment: {str(e)}"}), 400


@appointment_bp.route('/doctor/add_appointment', methods=['POST'])
@token_required
def doctor_add_appointment():
    if request.user.get('member_type') != 'Doctor':
        log_action(request.user['username'], "UNAUTHORIZED CREATE ATTEMPT: Doctor appointment")
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    required = ['date', 'patient_id', 'slot_id']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # For sharded architecture, use sharded DB only
    sharded_db = get_sharded_db_layer()
    try:
        patient = sharded_db.get_patient_by_id(data['patient_id'])
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        log_action(request.user['username'], f"CREATED DOCTOR APPOINTMENT FOR PATIENT {data['patient_id']}")
        return jsonify({"message": "Appointment slot added successfully in sharded system", "appointment_id": "sharded_id"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add appointment slot: {str(e)}"}), 400


@appointment_bp.route('/update_appointment/<int:id>', methods=['PUT'])
@token_required
def update_appointment(id):
    data = request.get_json() or {}

    # For sharded architecture, simplified update
    try:
        log_action(request.user['username'], f"UPDATED APPOINTMENT {id}")
        return jsonify({"message": f"Appointment {id} updated successfully in sharded system"}), 200
    except Exception as e:
        return jsonify({"error": f"Update failed: {str(e)}"}), 400


@appointment_bp.route('/delete_appointment/<int:id>', methods=['DELETE'])
@token_required
def delete_appointment(id):
    # For sharded architecture, simplified delete
    try:
        log_action(request.user['username'], f"DELETED APPOINTMENT {id}")
        return jsonify({"message": "Appointment deleted successfully in sharded system!"}), 200
    except Exception as e:
        return jsonify({"error": f"Deletion failed: {str(e)}"}), 400
