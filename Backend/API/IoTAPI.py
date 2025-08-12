import json
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import redis_client
from ..Service import UpdateIotDeviceStateService # Pretpostavimo da imate ovakav servis


# Kreiranje Blueprint-a za organizaciju IoT ruta
iot_bp = Blueprint('iot', __name__)

@iot_bp.route("/iot/update-state", methods=["POST"])
@jwt_required()
def update_iot_device_state():
    """
    Endpoint za promenu stanja IoT uređaja.
    Nakon promene, invalidira (briše) keš za live merenje kako bi se podaci
    odmah ažurirali pri sledećem pozivu.
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        device_id = data.get("device_id")
        new_state = data.get("is_active")

        if device_id is None or new_state is None:
            return jsonify({"error": "Missing device_id or is_active parameter"}), 400

        # Pozivanje servisa koji ažurira stanje u bazi podataka
        success = UpdateIotDeviceStateService(device_id, new_state, user_id)
        if not success:
            return jsonify({"error": "Failed to update device state"}), 500

        # --- KLJUČNI DEO: INVALIDACIJA KEŠA ---
        # Brišemo keširani ključ za live merenje.
        # Sledeći put kada korisnik zatraži podatke, doći će do "cache miss"-a
        # i podaci će biti ponovo proračunati.
        cache_key = f"live_metering_data:{user_id}"
        redis_client.delete(cache_key)

        return jsonify({"message": "Device state updated successfully and cache invalidated."}), 200

    except Exception as e:
        print(f"An unexpected error occurred in update_iot_device_state endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
