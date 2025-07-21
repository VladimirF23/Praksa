from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import redis
import os
from configJWT import Config            #moja config klasa
from dotenv import load_dotenv


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

# Getter to use in other modules
def get_redis_client():
    return redis_client