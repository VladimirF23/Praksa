import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import redis_client
from ..Service import *

# Kreiranje Blueprint-a za organizaciju IoT ruta
iot_bp = Blueprint('iot', __name__)

@iot_bp.route("/iot/update-state", methods=["POST"])
@jwt_required()
def update_iot_device_state():
    """
    Endpoint za promenu stanja IoT uređaja.
    Nakon promene, invalidira (brise) cache za live merenje kako bi se podaci
    odmah aaurirali pri sledecem pozivu.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        device_id = int(data.get("device_id"))
        new_state = data.get("is_active")

        if device_id is None or new_state is None:
            return jsonify({"error": "Missing device_id or is_active parameter"}), 400

        # Pozivanje servisa koji azurira stanje u bazi podataka
        success = UpdateIotDeviceStateService(device_id, new_state, user_id)
        if not success:
            return jsonify({"error": "Failed to update device state"}), 500

        # --- INVALIDACIJA CACHE-a ---
        # obrisacemo ovo i onda u live meteringu ce morati da ide do baze da pokupi iot uredjaje

        cache_key = f"user_iot_devices:{user_id}"
        redis_client.delete(cache_key)

        return jsonify({"message": "Device state updated successfully"}), 200

    except Exception as e:
        print(f"An unexpected error occurred in update_iot_device_state endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
    

@iot_bp.route("/iot/update-priority", methods=["POST"])
@jwt_required()
def update_iot_device_priority():
    """
    Endpoint for changing the priority level of an IoT device.
    Invalidates the live metering cache after the change.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        device_id = int(data.get("device_id"))
        new_priority = data.get("new_priority")

        # Sanitize and validate the new priority against allowed ENUM values
        allowed_priorities = ['critical', 'medium', 'low', 'non_essential']
        if new_priority not in allowed_priorities:
             return jsonify({"error": f"Invalid priority level. Must be one of: {', '.join(allowed_priorities)}"}), 400

        if device_id is None or new_priority is None:
            return jsonify({"error": "Missing device_id or new_priority parameter"}), 400

        

        print(f"DEBUG: Attempting to set Device {device_id} priority to {new_priority} for user {user_id}")
        
        success = UpdateIotDevicePriorityService(device_id, new_priority, user_id)
        if not success:
             return jsonify({"error": "Failed to update device priority or device not found"}), 500

        # --- INVALIDACIJA CACHE-a ---
        cache_key = f"user_iot_devices:{user_id}"
        redis_client.delete(cache_key)

        return jsonify({"message": "Device priority updated successfully"}), 200

    except Exception as e:
        print(f"An unexpected error occurred in update_iot_device_priority endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500