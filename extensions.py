
#extensions.py
from gevent import monkey                                       #za python debuger
monkey.patch_all()


from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import redis
import os
from configJWT import Config            #moja config klasa
from dotenv import load_dotenv
import json
from flask_socketio import SocketIO

import logging
logging.basicConfig(level=logging.DEBUG)            #za socketoi logovoanje


app = Flask(__name__)
app.config.from_object(Config)   #Config sadrzi parametre za jwt token, a dole skroz se kreira jwt preko JWTManager-a
CORS(app, resources={r"/*": {
    "origins": ["https://localhost", "http://localhost:3000"],          # Dozvoljavamo oba Nginx (HTTPS) i direct React dev server (HTTP)
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],             # Osiguravamo sve metode koriscene od strane frontend-a da budu dozvoljene
    "allow_headers": ["Content-Type", "Authorization", "X-CSRF-Token"], # Ekplicitno dozvoljavamo header-e koriscene u request-u
    "supports_credentials": True                                        # MORA True za cookies (ukljucuci HttpOnly JWTs and CSRF) da bi radili preko svih origins/ports
}})

load_dotenv(os.path.join(os.path.dirname(__file__), "devinfoDocker.env"))
redis_password = os.getenv("REDIS_PASSWORD")

#Redis localhost port je setupovan u Config-u  stavi ovo da se conectuje na redis conteiner
redis_client = redis.StrictRedis(
    host="redis-praksa",       #ime service
    port=6379,
    password= redis_password, 
    decode_responses=True  # Automatically decode strings da ne budu u byte-ovima
)

# provera da li redis radi
try:
    redis_client.ping()
    print("Connected to Redis successfully!")
except redis.ConnectionError:
    print("Failed to connect to Redis.")

jwt = JWTManager(app)


# Inicijalizacija Flask-SocketIO
# Postavljanje CORS-a za SocketIO, mora biti isto kao i za Flask aplikaciju
# async_mode='gevent' je preporučeni mod za performanse

#OVDE JE MOZDA GRESKA ZBOG http://localhost:3000"

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent',
                    ping_interval=180, #                                    Pingovi za debugovanje posle se treba ju smanjiti, 180 -> 3 minuta, timeot 300 sek
                    ping_timeout=300,  #
                    logger=True, engineio_logger=True)



#cors_allowed_origins=["http://localhost:3000", "https://localhost","https://solartrack.local"]





# Getter da bi mogao drugde da ga koristim
def get_redis_client():
    return redis_client


def get_active_users_from_redis() -> list:
    """
    Dohvata listu aktivnih korisnika i njihove pune konfiguracije (solar, baterija, IoT)
    iz Redis kesa, na osnovu definisane seme kesiranja.
    
    Returns:
        Lista recnika, gde svaki recnik predstavlja aktivnog korisnika sa svim
        konfiguracionim podacima. Vraca praznu listu ako nema aktivnih korisnika.
    """
    print("Dohvatam aktivne korisnike iz Redis-a...")
    
    active_users_data = []

    # Koristimo 'keys("user:*")' da pronađemo sve kljuceve aktivnih korisnika.
    # U produkciji sa mnogo kljuceva, 'scan' je bolji od 'keys'.
    user_keys = redis_client.keys("user:*")

    if not user_keys:
        print("Nema aktivnih korisnika u Redis kesu.")
        return active_users_data
    
    for user_key in user_keys:
        try:
            user_id = user_key.split(b':')[1].decode('utf-8')
            
            user_json = redis_client.get(user_key)
            if not user_json:
                continue
            user_data = json.loads(user_json.decode('utf-8'))
            
            solar_system_data = None
            solar_system_id_bytes = redis_client.get(f"user_solar_system_id:{user_id}")
            if solar_system_id_bytes:
                solar_system_id = solar_system_id_bytes.decode('utf-8')
                solar_system_json = redis_client.get(f"solar_system:{solar_system_id}")
                if solar_system_json:
                    solar_system_data = json.loads(solar_system_json.decode('utf-8'))
                    user_data["solar_system_config"] = solar_system_data
            
            battery_data = None
            if solar_system_data and solar_system_data.get('battery_id'):
                battery_id = solar_system_data['battery_id']
                battery_json = redis_client.get(f"battery:{battery_id}")
                if battery_json:
                    battery_data = json.loads(battery_json.decode('utf-8'))
                    user_data["battery_config"] = battery_data
            
            iot_devices_data = None
            iot_devices_json = redis_client.get(f"user_iot_devices:{user_id}")
            if iot_devices_json:
                iot_devices_data = json.loads(iot_devices_json.decode('utf-8'))
                user_data["iot_devices_data"] = iot_devices_data
            
            active_users_data.append(user_data)
            
        except (json.JSONDecodeError, IndexError, TypeError) as e:
            print(f"Greska prilikom obrade Redis kljuca '{user_key.decode('utf-8')}': {e}")
            continue

    print(f"Found {len(active_users_data)} active users ")
    return active_users_data