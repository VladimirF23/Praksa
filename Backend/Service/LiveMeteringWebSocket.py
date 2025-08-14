import json
import threading

from ..Service import *

import pandas as pd
import requests_cache
import openmeteo_requests
from retry_requests import retry
from flask import Blueprint, jsonify, current_app,request
from flask_jwt_extended import jwt_required, get_jwt_identity,decode_token
from extensions import redis_client, socketio, get_active_users_from_redis
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler

from flask_socketio import SocketIO, join_room, emit

# Create a blueprint for organization
live_metering_bp = Blueprint('live_metering', __name__)

# Scheduler instance to run background tasks
scheduler = BackgroundScheduler()
scheduler.start()


def build_battery_cache_data(battery_id, battery_data):
    """
    Builds a battery cache data dictionary from the given battery data.
    
    Args:
        battery_id (int): Battery ID for the Redis key.
        battery_data (dict): Battery information from DB or calculations.

    Returns:
        dict: Battery cache payload.
    """
    return {
        "battery_id": battery_id,
        "system_id": battery_data.get("system_id"),
        "model_name": battery_data.get("model_name"),
        "capacity_kwh": battery_data.get("capacity_kwh"),
        "max_charge_rate_kw": battery_data.get("max_charge_rate_kw"),
        "max_discharge_rate_kw": battery_data.get("max_discharge_rate_kw"),
        "efficiency": battery_data.get("efficiency"),
        "manufacturer": battery_data.get("manufacturer"),
        "current_charge_percentage": battery_data.get("current_charge_percentage"),
        "last_cached_at": datetime.now().timestamp()
    }



# --- HELPER FUNCTION: Get Open-Meteo API Data ---
def get_live_irradiance(latitude, longitude, tilt, azimuth, user_id):
    """
    Helper function to call OpenMeteo API with cache and retry logic.
    Caches per user by adding user_id to the request parameters.
    Uses `global_tilted_irradiance_instant` for more precise measurements.
    """
    cache_session = requests_cache.CachedSession('.cache', expire_after = 60*15)        #15 min
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "minutely_15": ["global_tilted_irradiance_instant", "temperature_2m", "is_day"],
        "forecast_minutely_15": 1,
        "timezone": "auto",
        "tilt": tilt,
        "azimuth": azimuth,
        "user_id": user_id
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        minutely_15 = response.Minutely15()
        
        irradiance_data = minutely_15.Variables(0).ValuesAsNumpy()
        temperature_data = minutely_15.Variables(1).ValuesAsNumpy()
        is_day_data = minutely_15.Variables(2).ValuesAsNumpy()
        
        offset = pd.Timedelta(seconds=response.UtcOffsetSeconds())
        
        minutely_15_data = {
            "date": pd.date_range(
                start=pd.to_datetime(minutely_15.Time(), unit="s", utc=False) + offset,
                end=pd.to_datetime(minutely_15.TimeEnd(), unit="s", utc=False) + offset,
                freq=pd.Timedelta(seconds=minutely_15.Interval()),
                inclusive="left"
            ),
            "global_tilted_irradiance_instant": irradiance_data,
            "temperature_2m": temperature_data,
            "is_day": is_day_data
        }
        
        minutely_15_dataframe = pd.DataFrame(data=minutely_15_data)
        
        if not minutely_15_dataframe.empty:
            return minutely_15_dataframe.iloc[0].to_dict()
        
        return None
        
    except Exception as e:
        print(f"Error calling Open-Meteo API: {e}")
        return None

#TODO dodaj da ako je vec izracunati podaci da se samo uzme iz cache-a da bih sprecio da kada user se npr logoutuje i ponovo udje da mu smanji % baterije za 2 puta
def calculate_and_emit_live_data(user_id):
    """
    Performs all the live metering calculations and emits the data via WebSocket.
    This function can be called from multiple places:
    1. The background scheduler (every 15 minutes)
    2. A user action (e.g., turning on an IoT device)
    """
    #with current_app.app_context():  OVO JE NESTO ZA THREAD-OVE
    try:
            cache_key = f"live_metering_data:{user_id}"
            
            live_data_payload_cache= None

            #da sprecimo da se funkcija izvrsava vise puta u 15 min (da ne bi svake sekunde sa povecavao % baterije / smanjivao )
            live_data_payload_cache = redis_client.get(f"live_metering_data:{user_id}")

            if live_data_payload_cache:
                live_data_payload_cache = json.loads(live_data_payload_cache);    

                socketio.emit('live_metering_data', live_data_payload_cache, room=f"user_{user_id}")
                print(f"Emitted CACHE data for user {user_id}")
                return
                 

            # --- Fetching data from Redis with fallback to DB ---
            system_id = None
            battery_id = None
            system_id_str = redis_client.get(f"user_solar_system_id:{user_id}")
            if system_id_str:
                system_id = int(system_id_str)
                battery_id_str = redis_client.get(f"solar_system_battery_id:{system_id}")
                if battery_id_str: 
                    battery_id = int(battery_id_str)
            
            #  Redis pipeline da fetchujemo podatke brzo
            pipe = redis_client.pipeline()
            keys_to_fetch = [f"user:{user_id}", f"user_iot_devices:{user_id}"]
            pipe.get(f"user:{user_id}")
            pipe.get(f"user_iot_devices:{user_id}")
            
            if system_id:
                keys_to_fetch.append(f"solar_system:{system_id}")
                pipe.get(f"solar_system:{system_id}")
            if battery_id:
                keys_to_fetch.append(f"battery:{battery_id}")
                pipe.get(f"battery:{battery_id}")
            
            results = pipe.execute()
            cached_data_raw = {keys_to_fetch[i]: results[i] for i in range(len(keys_to_fetch))}
            
            # Deserialize cached data
            user_data = json.loads(cached_data_raw.get(f"user:{user_id}")) if cached_data_raw.get(f"user:{user_id}") else None
            iot_devices_cache = json.loads(cached_data_raw.get(f"user_iot_devices:{user_id}")) if cached_data_raw.get(f"user_iot_devices:{user_id}") else None

            #moramo ovako uzeti iot_devices posto sam ga cudno sacuvao
            iot_devices_data = iot_devices_cache.get("devices", []) if iot_devices_cache else []
            solar_system_data = json.loads(cached_data_raw.get(f"solar_system:{system_id}")) if system_id and cached_data_raw.get(f"solar_system:{system_id}") else None
            battery_data = json.loads(cached_data_raw.get(f"battery:{battery_id}")) if battery_id and cached_data_raw.get(f"battery:{battery_id}") else None
            
            # Fallback ka DB-u ako cache-a nema
            if not user_data:
                user_data = GetUserByIdService(user_id)
                if user_data:
                    redis_client.setex(f"user:{user_id}", 3600, json.dumps(user_data))
                else:
                    print(f"Error: User data not found for user {user_id}")
                    return
            
            if not solar_system_data and user_data:
                solar_system_data_from_db = GetSolarSystemByUserIdService(user_id)
                if solar_system_data_from_db:
                    solar_system_data = solar_system_data_from_db
                    system_id = solar_system_data['system_id']
                    redis_client.setex(f"solar_system:{system_id}", 3600, json.dumps(solar_system_data))
                    redis_client.set(f"user_solar_system_id:{user_id}", str(system_id))
                else:
                    print(f"CRITICAL ERROR: User {user_id} found, but no solar system data in DB.")
                    return
            
            if not battery_data and solar_system_data and solar_system_data.get("battery_id"):
                battery_id_from_solar_system = solar_system_data["battery_id"]
                battery_data_from_db = GetBatteryDataService(battery_id_from_solar_system)
                if battery_data_from_db:
                    battery_data = battery_data_from_db
                    redis_client.setex(f"battery:{battery_id_from_solar_system}", 1800, json.dumps(battery_data))
                    redis_client.set(f"solar_system_battery_id:{solar_system_data['system_id']}", str(battery_id_from_solar_system))
            
            if not iot_devices_data and user_data:
                iot_devices_data_from_db = GetUsersIOTsService(user_id)
                if iot_devices_data_from_db:
                    iot_devices_data = iot_devices_data_from_db
                    redis_client.setex(f"user_iot_devices:{user_id}", 600, json.dumps(iot_devices_data))
            
            # Check for required data
            if not all([user_data.get('latitude'), user_data.get('longitude'), solar_system_data.get('total_panel_wattage_wp')]):
                print(f"Error: Incomplete solar system data for user {user_id}")
                return
            
            latitude = user_data.get('latitude')
            longitude = user_data.get('longitude')
            tilt = solar_system_data.get('tilt_degrees', 30)
            azimuth = solar_system_data.get('azimuth_degrees', 180)
            
            live_data = get_live_irradiance(latitude, longitude, tilt, azimuth, user_id)
            if not live_data:
                print(f"Error: Failed to fetch live weather data for user {user_id}")
                return
            
            current_gti = round(live_data.get("global_tilted_irradiance_instant", 0), 2)  # na 2 decimale zbog preciznosti
            current_temperature = round(live_data.get("temperature_2m", 0), 2)            
            current_is_day = live_data.get("is_day")
            
            # pozivanje funkcije koja racunaju
            solar_production_kw = calculate_solar_production(solar_system_data, {"global_tilted_irradiance_instant": current_gti, "temperature_2m": current_temperature, "is_day": current_is_day})
            
            solar_production_kw = round(solar_production_kw,2)

            household_consumption_kw = calculate_household_consumption(solar_system_data, iot_devices_data)

            household_consumption_kw = round(household_consumption_kw,2)
            
            net_power_kw = solar_production_kw - household_consumption_kw

            #DODAJ IF ako ne postoji baterija da se ovo ne racuna
            new_charge_percentage, battery_flow_kw = update_battery_charge(battery_data, net_power_kw, time_step_hours=1)

            battery_flow_kw = round(battery_flow_kw,2)
            new_charge_percentage = round(new_charge_percentage,2)                      #100.00, 95.23 je ok, a d abi moglo norm da se upise

            grid_contribution_kw = calculate_grid_contribution(solar_production_kw, household_consumption_kw, battery_flow_kw)
            
            live_data_payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "solar_production_kw": round(solar_production_kw, 2),
                "household_consumption_kw": round(household_consumption_kw, 2),
                "battery_charge_percentage": round(new_charge_percentage, 2),
                "battery_flow_kw": round(battery_flow_kw, 2),
                "global_tilted_irradiance_instant": current_gti,
                "grid_contribution_kw": round(grid_contribution_kw, 2),
                "current_temperature_c": round(current_temperature, 1),
                "is_day": bool(current_is_day)
            }
            
            #DODAJ IF DA AKO NE POSTOJI BATERIJA DA SE OVO NE RACUNA , MSM da nema potrebe za if-om
            flag = UpdateBatteryCurrentPercentageService(battery_id, new_charge_percentage)

            # Ovo bukvalno ne treba jer ako je na 100% i na 0% vise puta onda ce bez razloga fail-ovati jer tamo nam vraca kao na changed row true ili false 
            # if flag is False:
            #     print(f"Error: Failed to update battery percentage for user {user_id}")
            #     return

            # Treba i reddis updejtovati kao sto smo i bazu updejtovali, Posto mi je ovde bio problem jer nisam u reddi-su updejtovao battery_percentage i onda je on  istao isti kao pre prvog izvrsavanja
            # i kada je otislo do baze onaj current_row se nije promenio posto je u bazi bilo upsiano 45 a u redisu je ostalo 75 kao originalno i onda je current row bio kao da se nista nije promenilo i ovde mi je bacalo false

            battery_data["current_charge_percentage"] = new_charge_percentage
            
            battery_cache_data = build_battery_cache_data(battery_data["battery_id"], battery_data)     #dodao sam i onaj timestamp kao u svakom cache-ovanju

            redis_client.setex(f"battery:{battery_id}", 1800, json.dumps(battery_cache_data))



            #Trebala bi ovde mozda automatizacija za IOT uredjaje

            redis_client.setex(cache_key, 900, json.dumps(live_data_payload))                           #15 minuta da traje cache, 900, testirano i na 30 sekundi radi sve norm
            
            # Emit data to the connected user via WebSocket
            socketio.emit('live_metering_data', live_data_payload, room=f"user_{user_id}")
            print(f"Emitted new data for user {user_id}")

    except Exception as e:
        print(f"An unexpected error occurred during calculation for user {user_id}: {e}")

# --- WEB SOCKET HANDLERS ---
@socketio.on('connect')
def handle_connect():
    print("--- [DEBUG] handle_connect function entered ---")
    
    # Print all cookies to see what the server is actually receiving.
    print("--- [DEBUG] Received cookies: ---")
    for name, value in request.cookies.items():
        print(f"  Cookie: {name} = {value}")
    print("-----------------------------------")
    
    token = request.cookies.get('access_token_cookie')
    print(f"--- [DEBUG] Access token {'found' if token else 'NOT found'} ---")

    if not token:
        print("Client attempted to connect without a token. Disconnecting.")
        return False

    try:
        print("--- [DEBUG] Attempting to decode token ---")
        decoded_token = decode_token(token)
        user_id = decoded_token['sub']

        join_room(f"user_{user_id}")
        print(f"--- [DEBUG] Client connected and authenticated for user {user_id} ---")

        #prvo cu bez thread-ova da bih mogao da debagujem i da proverim sve kalkulacije

        #threading.Thread(target=calculate_and_emit_live_data, args=(int(user_id),)).start()

        calculate_and_emit_live_data(user_id)

        print("--- [DEBUG] Started data calculation ---")

    except Exception as e:
        print(f"--- [ERROR] Token verification failed for client. Disconnecting. Error: {e} ---")
        return False


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

# # --- BACKGROUND TASK ---
# def scheduled_task_for_all_users():
#     print("Running scheduled task to update live metering for all users...")

#     # Pozivamo funkciju koja dohvaća sve aktivne korisnike iz Redisa
#     active_users = get_active_users_from_redis()

#     if not active_users:
#         print("No active users found to process.")
#         return

#     # Prolazimo kroz svakog aktivnog korisnika
#     for user_data in active_users:
#         # Pobrini se da je 'user_id' dostupan i prosledjen kao integer
#         user_id = user_data.get('user_id')
#         if user_id:
#             # Uvek kreiraj novi thread za svaki zadatak da ne bi blokirao scheduler
#             threading.Thread(target=calculate_and_emit_live_data, args=(int(user_id),)).start()
    
#     print("Scheduled task finished.")

# # Add the scheduled job to run every 15 minutes

# OVDE JE PROBLEM JER CE 2 PUT SCHEDULE-OVATI OVAJ POSAO OVO SE TREBA NEGDE IZMESTITI, a i da se 2 puta scheduluje svakako ce biti u cache-u pa nece nista naknadno racunati
# scheduler.add_job(scheduled_task_for_all_users, 'interval', minutes=15)

# --- OLD ENDPOINT REMOVED. New logic is handled by WebSockets and background tasks. ---
# Note: You would still have a REST endpoint for IoT device updates, which would
# also trigger a call to calculate_and_emit_live_data.
