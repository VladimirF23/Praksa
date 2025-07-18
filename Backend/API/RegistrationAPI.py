from ..Service import *
from flask import Blueprint, request,jsonify,make_response
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt,decode_token,set_access_cookies,set_refresh_cookies,get_csrf_token
from datetime import timedelta,datetime
from extensions import jwt,redis_client   

import redis

#Check Redis connection on app startup
try:
    redis_client.ping()  # Test Redis connection
except redis.ConnectionError:
    raise Exception("Failed to connect to Redis.")

#metoda je post jer POST drzi sensitive data (email/password) u request body a on nije logovan u browser history
registration_blueprint = Blueprint('registration',__name__,url_prefix='/registration')


@registration_blueprint.route('', methods =['POST'])
def register_user():
    """
        Sa Front-a Dobijemo podatke vezane za user-a -> koji idu u user's table
        Vazan je redosled ubacivanja u bazu podataka prvo trebamo user-a, bateriju ili iot(posto zavise od user-a), solar configuaricju (posto moze izabrati user odredjenu bateriju)


        Dobijemo podatke vezane za IoT
        Dobijemo podatke vezane za Bateriju korisnika
        Dobijemo podatke vezane za Solar System
    """
    try:
        user_data =request.get_json()
        #username,email,password
        if not user_data:
            return jsonify({"error":"Invalid JSON format"}),400
        

        #pitaj chat gpt da li je moguce posto ovde imamo proveru, da nekako user pogodi one metode u Engine layeru i onda da zato moramo da imamo provere na vise layer-a
        required_fields =["username", "email", "password"]
        missing_fields =[field for field in required_fields if field not in user_data]

        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400

        #service layer zovemo
        RegisterUserService(user_data)

        #Posto je potrebn da takodje kreiramo JWT token prilikom registracije a ja sam se ogranicio da se unutar MysqlDB generise id user-a 
        #necemo moci da uzmemo id bez da se loginujemo pa cu samo iskoristiti funkciju iz logina i logiku iz logina

        #mysql ce vratiti dict posto sam stavio da kod cursora dict=True
        user =  LoginUserService(user_data)

        access_token = create_access_token(
            identity=str(user["id"]),
            additional_claims={
                "username": user["username"],           
                "global_admin": user["global_admin"]    
            },
            expires_delta=timedelta(minutes=15) # 20 sekundi za testiranje
        )
        
        refresh_token = create_refresh_token(
            identity=str(user["id"]),
            additional_claims={
                "username": user["username"],           
                "global_admin": user["global_admin"]   
            },
            expires_delta=timedelta(days=7) 
        )

        decoded_access  = decode_token(access_token)
        decoded_refresh = decode_token(refresh_token)

        access_jti  = decoded_access["jti"]
        refresh_jti = decoded_refresh["jti"]

        user_metadata_access = {
                "user_id": user["id"],
                "username": user["username"],
                "global_admin": user["global_admin"],
                "status": "valid",
                "issued_at": decoded_access["iat"],  # epoch
                "expires": decoded_access["exp"],     # epoch
                "type" : "access_token"

        }
        user_metadata_refresh = {
                "user_id": user["id"],
                "username": user["username"],
                "global_admin": user["global_admin"],
                "status": "valid",                    #necu menjati ovo samo cu blacklistovati token...
                "issued_at": decoded_refresh["iat"],  # epoch
                "expires": decoded_refresh["exp"],     # epoch
                "type" : "refresh_token"

        }




        pipe = redis_client.pipeline()

        #queu-jem komande na pipe i na execute-u se sve izvrse i tako izbegnem da se delimicno izvrse
        pipe.setex(f"access_token:{access_jti}",int(timedelta(minutes=15).total_seconds()),json.dumps(user_metadata_access))    
        pipe.setex(f"refresh_token:{refresh_jti}",int(timedelta(days=7).total_seconds()),json.dumps(user_metadata_refresh))

        #dodajemo sve id tokena koji pripadaju user-u, ukljucujuci i refresh token
        pipe.sadd(f"user_tokens:{user['id']}", access_jti, refresh_jti)

        pipe.execute()

        #novi accses stavljamo u secure cookie
        response = make_response(jsonify({"message": "User Registered in successfully"}))
        set_access_cookies(response, access_token)
        set_refresh_cookies(response,refresh_token)


        # CSRF token se GENERISAO VEC zasebno u JWT tokenu jer smo stavili JWT_COOKIE_CSRF_PROTECT = True
       



    except IlegalValuesException  as e:
        return jsonify({"error":str(e)}), 400
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500 
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500