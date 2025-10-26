from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import redis_client # Assuming redis_client is available
from ..Service import * # Assuming your battery services are here

# Kreiranje Blueprint-a za organizaciju Battery ruta
battery_bp = Blueprint('battery', __name__)


@battery_bp.route("/battery/add", methods=["POST"])
@jwt_required()
def add_battery():
    """
    Endpoint za dodavanje nove baterije. 
    Ako korisnik vec ima bateriju, ova ruta bi trebalo da je azurira (UPSERT).
    Vraca novododatu/azuriranu bateriju.
    """
    try:
        user_id = get_jwt_identity()
        battery_data = request.get_json()

        if not battery_data:
            return jsonify({"error": "Missing battery data"}), 400
        

        #current_charge_percentage predefined da vidim da li radi
        battery_data["current_charge_percentage"] = 50
        new_battery = RegisterBatteryService(battery_data)
        
        solar_System_id = GetSolarSystemIdByUserIdService(user_id)

        #AddSolarSystemToBattery
        #dodamo u battery tabeli id solarnog sistema
        AddSolarSystemToBatteryService(new_battery["battery_id"],solar_System_id)

        new_battery["system_id"] = solar_System_id

        if not new_battery:
            return jsonify({"error": "Failed to register or update battery."}), 500
        

        #dodamo u solarnom sistemu tabeli id baterije nove

        # 2. Update the 'solar_systems' table with the new battery ID
        # Use the new function we defined above
        UpdateSolarSystemBatteryIdService(solar_System_id, new_battery["battery_id"])


        user_solar_system_key = f"user_solar_system_id:{user_id}" # Maps user to system ID
        solar_system_data_key = f"solar_system:{solar_System_id}" # The main system data, now stale
        # Batch delete the two keys that are now stale
        redis_client.delete(user_solar_system_key, solar_system_data_key) 

        return jsonify({
            "message": "Battery added/updated successfully.", 
            # Vraca ceo objekat baterije kako bi frontend mogao da updejtuje Redux stanje direktno
            "battery": new_battery 
        }), 200

    except Exception as e:
        print(f"An unexpected error occurred in add_battery endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

# --- ENDPOINT 2: DELETE BATTERY ---
@battery_bp.route("/battery/delete", methods=["POST"])
@jwt_required()
def delete_battery():
    """
    Endpoint za brisanje baterije povezane sa korisnikom.
    """
    try:
        data = request.get_json()

        battery_id_to_delete = data.get('battery_id')
        solar_system_id_to_delete = data.get('solar_system_id')

        user_id = get_jwt_identity()

        # 1. Pozivanje servisa za brisanje baterije

        success = DeleteBatteryForUserService(int(battery_id_to_delete))
        
        if not success:
            # Vracamo 404 ako baterija nije ni postojala (ili 500 ako je doslo do greske u bazi)
            return jsonify({"error": "Failed to delete battery or battery not found."}), 404
        
        # --- Cache keys to delete: ---
        battery_key = f"battery:{battery_id_to_delete}" # Cache for the battery itself (correct)
        system_battery_link_key = f"solar_system_battery_id:{solar_system_id_to_delete}" # Link (correct)
        user_solar_system_key = f"user_solar_system_id:{user_id}" # User->System ID mapping (correct)
        
    
        solar_system_data_key = f"solar_system:{solar_system_id_to_delete}"
        # -----------------------------
        
        # You can delete them all at once:
        redis_client.delete(
            battery_key, 
            system_battery_link_key, 
            user_solar_system_key, 
            solar_system_data_key # ADDED
    )

        return jsonify({
            "message": "Battery deleted successfully."
        }), 200

    except Exception as e:
        print(f"An unexpected error occurred in delete_battery endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500