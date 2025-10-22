
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
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta


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


#  For Cellery Define the Redis URL for the SocketIO message queue
# ------------------------------------------------------------------
redis_host = 'redis-praksa'
redis_port = 6379
redis_db = 0
redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"



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
                    logger=True,message_queue=redis_url ,engineio_logger=True)



#cors_allowed_origins=["http://localhost:3000", "https://localhost","https://solartrack.local"]


# from apscheduler.schedulers.background import BackgroundScheduler

# scheduler = BackgroundScheduler()
# scheduler.start()


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
    

    # Koristimo 'keys("user:*")' da pronadjemo sve kljuceve aktivnih korisnika.
    # U produkciji sa mnogo kljuceva, 'scan' je bolji od 'keys'.
    user_keys = redis_client.keys("user:*")
    user_ids = [key.split(":")[1] for key in user_keys]

    if not user_keys:
        print("Nema aktivnih korisnika u Redis kesu.")
        return []
    

    print(f"Found {len(user_keys)} active users ")
    return user_ids



