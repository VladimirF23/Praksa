from ..Service import *
from flask import Blueprint, request,jsonify,make_response
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt,decode_token,set_access_cookies,set_refresh_cookies,get_csrf_token,get_jwt_identity
from datetime import timedelta,datetime
from extensions import jwt,redis_client   

import redis

auth_blueprint  = Blueprint("auth",__name__,url_prefix="/auth")


@auth_blueprint.route('/login',methods=['POST'])
# metoda je post jer POST drzi sensitive data (email/password) u request body a on nije logovan u browser history #Get exposuje parametre u URL sto nije sigurno
# primaran posao login-a kada koristimo HttpOnlyCookie je da setuje accsess i refresh tokene kao Cooki-e koje JS ne moze da pristupi
# i vraca se poruka Uspesan login ali se ne vraca JWT ili user data Browser ce dobiti Set-Cookie headers i automatski store-vati HttpOnly cookie i JS citljiv CSRF cookie
# Front end ne moze da procita JWT cookie zato sto su HttpOnly i ne moze da vidi info o user-u (username,id,global_admin)
# Odma nakon uspesnog logina na frontu se salje request na API da se za sada loginovanog user-a posalje info da bi React mogao to da prikazuje na UI-u
def login():
    try:
        user_data = request.get_json()
        if not user_data:
            return jsonify({"error":"Invalid JSON format"}),400
        
        required_fields =["username", "password"]
        missing_fields =[field for field in required_fields if field not in user_data]

        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400
        
        #mysql ce vratiti dict posto sam stavio da kod cursora dict=True
        user =  LoginUserService(user_data)

        # --- Caching User Data ---
        # Cachujemo  (user:{user_id}) i dodatne podatke sa json.dumps
        # ako postoji, setex will owerwrituje  ga, effectively updating it.
        redis_client.setex(f"user:{user['user_id']}", 3600, json.dumps(user)) # Example TTL: 1 hour (3600 seconds)

        # Cache the mapping for solar system ID (user_solar_system_id:{user_id})
        # You'll need to fetch the solar_system_id if not already in the 'user' dict.
        # It's best to fetch this from the DB here if it's not part of the initial 'user' dict.
        solar_system_data = GetSolarSystemByUserIdService(user['user_id'])
        if solar_system_data:
            redis_client.set(f"user_solar_system_id:{user['user_id']}", str(solar_system_data['system_id']))
            # cachiramo solarni sistem ceo
            redis_client.setex(f"solar_system:{solar_system_data['system_id']}", 3600, json.dumps(solar_system_data))

            # Cache battery_id mapiranje ako solarni system ima bateriju
            if solar_system_data.get('battery_id'):
                redis_client.set(f"solar_system_battery_id:{solar_system_data['system_id']}", str(solar_system_data['battery_id']))

                battery_data = GetBatteryDataService(solar_system_data['battery_id'])
                if battery_data:
                    redis_client.setex(f"battery:{solar_system_data['battery_id']}", 1800, json.dumps(battery_data))
        else:
            print(f"WARNING: No solar system found for user {user['user_id']} during login.")

         # Cache IoT devices (ako postoje)
        iot_devices_data = GetUsersIOTsService(user['user_id'])
        if iot_devices_data:
             redis_client.setex(f"user_iot_devices:{user['user_id']}", 600, json.dumps(iot_devices_data))


        access_token = create_access_token(
            identity=str(user["user_id"]),
            additional_claims={
                "username": user["username"],           
                "user_type": user["user_type"]  # Changed from "global_admin"
            },
            expires_delta=timedelta(minutes=15) # 20 sekundi za testiranje
        )
        
        refresh_token = create_refresh_token(
            identity=str(user["user_id"]),
            additional_claims={
                "username": user["username"],           
                "user_type": user["user_type"]  # Changed from "global_admin"
            },
            expires_delta=timedelta(days=7) 
        )

        #JWT_COOKIE_SECURE = True -> kaze Flask-JWT-Extended da JWT cookie  salje SAMO preko HTTPS (secure connection), da ne bi preko HTTP i tako sprecava man i middle attack
        #JWT_COOKIE_CSRF_PROTECT = True -> drugi CSRF token se pravi (random string razlicit od JWT tokena) i on se MORA slati u custom header-u (X-CSRF token)
        # sa svakim state changing reqeustom POST,PUT,DELETE etc, AKO CSRF token u headeru ne matchuje ona u cookie-u request se odbija

        # OVO JE BITNO JER:
        #jer cak i sa HttpOnly, moj browser ce automatski attach cookies na requests — ukljucijuci i one triggere-ovane od attacker (preko malicious <form> ili <script>).
        #CSRF protection zaustavlja ne-authorizovane komande da budu izvrsene SA strane user-a samo zato sto njegov browser auto-attachuje cookie-je.


        decoded_access  = decode_token(access_token)
        decoded_refresh = decode_token(refresh_token)

        access_jti  = decoded_access["jti"]
        refresh_jti = decoded_refresh["jti"]


        user_metadata_access = {
            "user_id": user["user_id"], 
            "username": user["username"],
            "user_type": user["user_type"], 
            "status": "valid",                      # Kljucno za revokaciju
            "issued_at": decoded_access["iat"],  # epoch
            "expires": decoded_access["exp"],    # epoch
            "type" : "access_token"
        }
        user_metadata_refresh = {
            "user_id": user["user_id"], 
            "username": user["username"], 
            "user_type": user["user_type"], 
            "status": "valid", 
            "issued_at": decoded_refresh["iat"],  
            "expires": decoded_refresh["exp"],    
            "type" : "refresh_token"
        }

        pipe = redis_client.pipeline()

        #queu-jem komande na pipe i na execute-u se sve izvrse i tako izbegnem da se delimicno izvrse
        pipe.setex(f"access_token:{access_jti}",int(timedelta(minutes=15).total_seconds()),json.dumps(user_metadata_access))    
        pipe.setex(f"refresh_token:{refresh_jti}",int(timedelta(days=7).total_seconds()),json.dumps(user_metadata_refresh))

        #dodajemo sve id tokena koji pripadaju user-u, ukljucujuci i refresh token
        pipe.sadd(f"user_tokens:{user["user_id"]}", access_jti, refresh_jti)





        pipe.execute()

        #novi accses stavljamo u secure cookie
        response = make_response(jsonify({"message": "User Logged in successfully"}))
        set_access_cookies(response, access_token)
        set_refresh_cookies(response,refresh_token)


        # CSRF token se GENERISAO VEC zasebno u JWT tokenu jer smo stavili JWT_COOKIE_CSRF_PROTECT = True
       

        return response,201

    except NotFoundException as e: 
        return jsonify({"error": str(e)}), 401 # Unauthorized or Bad Request for invalid credentials
    except IlegalValuesException as e:          # Catch validation errors from deeper layers
        return jsonify({"error": str(e)}), 400
    except ConnectionException as e:            
        return jsonify({"error": str(e)}), 500
    except Exception as e: 
        print(f"An unexpected error occurred during login: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500    

    

#ispravi ovo
@auth_blueprint.route('/admin', methods=['GET'])
@jwt_required()
def admin_only():
    try:
        # Get the identity of the current user (e.g., user_id) if needed for logging
        user_id = get_jwt_identity()

        # Get the entire JWT payload (claims)
        jwt_claims = get_jwt()


        user_type = jwt_claims.get("user_type") 


        if user_type != "admin": #
            print(f"Unauthorized access attempt to /admin by user_id: {user_id}, user_type: {user_type}")
            return jsonify({"error": "Forbidden: Admin access required"}), 403

        return jsonify({"message": f"Welcome, Admin {user_id}!"}), 200

    except Exception as e:
        print(f"An unexpected error occurred in /admin endpoint: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500


# Ovo se automatski poziva nakon uspesnog logina sa strane front-a i ovako osiguravam da login imao single responsability a to je set-ovanje access/refresh/csrf tokena
# Ovo ce user na frontu imati u svom redux-u
#pogledaj u notepadu sam objasnio zasto ovako 
@auth_blueprint.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_details():
    try:
        user_id = int(get_jwt_identity())

        # --- Uzimamo potrebne kljuceve za Redis ---

        # kljucevi u redisu su storovani za         pipe.setex(f"solar_system:{solar_system_id}", 3600, json.dumps(solar_system_cache_data))
        # i onda nam treba syste_id a to dobijamo preko drugog cache koji stoji vecno        
        #  pipe.set(f"user_solar_system_id:{user_id}", str(solar_system_id))                      


        system_id = None
        battery_id = None

        system_id_str = redis_client.get(f"user_solar_system_id:{user_id}")
        if system_id_str:
            system_id = int(system_id_str)
            battery_id_str = redis_client.get(f"solar_system_battery_id:{system_id}")
            if battery_id_str: 
                battery_id = int(battery_id_str)

        # --- Phase II: Build-ujemi i executujemo pipe za odredjene IDs ---
        pipe = redis_client.pipeline()
        keys_to_fetch = [] 

        keys_to_fetch.append(f"user:{user_id}")
        pipe.get(f"user:{user_id}")

        keys_to_fetch.append(f"user_iot_devices:{user_id}")
        pipe.get(f"user_iot_devices:{user_id}")

        if system_id:
            keys_to_fetch.append(f"solar_system:{system_id}")
            pipe.get(f"solar_system:{system_id}")
        if battery_id:
            keys_to_fetch.append(f"battery:{battery_id}")
            pipe.get(f"battery:{battery_id}")

        # Parse JSON stringova
        results = pipe.execute()
        cached_data_raw = {keys_to_fetch[i]: results[i] for i in range(len(keys_to_fetch))}


        user_data = json.loads(cached_data_raw.get(f"user:{user_id}")) if cached_data_raw.get(f"user:{user_id}") else None
        iot_devices_data = json.loads(cached_data_raw.get(f"user_iot_devices:{user_id}")) if cached_data_raw.get(f"user_iot_devices:{user_id}") else None
        solar_system_data = json.loads(cached_data_raw.get(f"solar_system:{system_id}")) if system_id and cached_data_raw.get(f"solar_system:{system_id}") else None
        battery_data = json.loads(cached_data_raw.get(f"battery:{battery_id}")) if battery_id and cached_data_raw.get(f"battery:{battery_id}") else None


        # --- Phase III: Fallback ka Bazi Podataka i Cachiramo (ako su podaci istekli u Redis-u tj Cache missovali smo) ---

        # User Data (Ako ne postoji hasiran not user_data onda idemo do baze podataka u suprotnom nastavljamo dole)
        if not user_data:
            user_data = GetUserByIdService(user_id)
            if user_data:
                redis_client.setex(f"user:{user_id}", 3600, json.dumps(user_data))              #cachiramo podatke 
            else:
                return jsonify({"error": "User data not found"}), 404
        
        # Solar System Data, uzimamo solar sistem ako postoji validni podaci za user-a 
        if not solar_system_data and user_data: # Only try if user exists
            solar_system_data_from_db = GetSolarSystemByUserIdService(user_id)
            if solar_system_data_from_db:
                solar_system_data = solar_system_data_from_db
                system_id = solar_system_data['system_id']
                redis_client.setex(f"solar_system:{system_id}", 3600, json.dumps(solar_system_data))
                redis_client.set(f"user_solar_system_id:{user_id}", str(system_id))
            else:
                # CRITICAL ERROR: User postoji a system na postoji.
                # Ovo ne sme da se desi
                print(f"CRITICAL ERROR: User {user_id} found, but no solar system data in DB.")
                return jsonify({"error": "Solar system data not found for user"}), 500             

        # Battery Data (opcionalno, zavisi da li uopste postoji solarni sistem da nije doslo do greske)
        if not battery_data and solar_system_data and solar_system_data.get("battery_id"):
            
            #solar_system_data.get("battery_id") osigurava da battery_id nije None i onda mogu poslati dole u service id lagano
            battery_id_from_solar_system = solar_system_data["battery_id"]
            battery_data_from_db = GetBatteryDataService(battery_id_from_solar_system)      #saljemo id baterije iz solarnog sistema
            if battery_data_from_db:
                battery_data = battery_data_from_db
                redis_client.setex(f"battery:{battery_id_from_solar_system}", 1800, json.dumps(battery_data))
                redis_client.set(f"solar_system_battery_id:{solar_system_data['system_id']}", str(battery_id_from_solar_system)) # Update mapping too

        # IoT Devices Data (optional)
        if not iot_devices_data and user_data: 
            iot_devices_data_from_db = GetUsersIOTsService(user_id)
            if iot_devices_data_from_db:
                iot_devices_data = iot_devices_data_from_db
                redis_client.setex(f"user_iot_devices:{user_id}", 600, json.dumps(iot_devices_data))


        # --- Phase IV: Pravimo Odgovor ---
        response_data = {
            "user": {
                "id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "user_type": user_data.get("user_type"),
                "house_size_sqm": user_data.get("house_size_sqm"),
                "num_household_members": user_data.get("num_household_members"),
                "latitude": user_data.get("latitude"),
                "longitude": user_data.get("longitude"),
                "registration_date": user_data.get("registration_date")
            },
            "solar_system": solar_system_data,
            "battery": battery_data,
            "iot_devices": iot_devices_data
        }

        # Brisemo 'last_cached_at' polja pre slanja ka frontend, to ne treba front da interesuje
        for key in ["user", "solar_system", "battery", "iot_devices"]:
            if response_data.get(key) and isinstance(response_data[key], dict) and "last_cached_at" in response_data[key]:
                del response_data[key]["last_cached_at"]
            elif response_data.get(key) and isinstance(response_data[key], list): # For IoT devices, iterate through the list
                for item in response_data[key]:
                    if isinstance(item, dict) and "last_cached_at" in item:
                        del item["last_cached_at"]

        return jsonify(response_data), 200

    except redis.RedisError as e:
        print(f"Redis Error in /me endpoint: {e}")
        return jsonify({"error": "Redis error", "details": str(e)}), 500

    except ConnectionException as e:
        print(f"Connection Error in /me endpoint: {e}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print(f"An unexpected error occurred in /me endpoint: {e}")
        return jsonify({"error": "Failed to retrieve user details", "details": str(e)}), 500
    


# ISPRAVI OVO

# Vazno pravilo posto mi je bitno da su podaci svezi cim se user logutuje brisemo i cachirane podatke i brisemo njegov access i refresh token ! mislim da tamo cemo i black listovati !!!

@auth_blueprint.route('/logout', methods=['POST'])
@jwt_required() # User must be logged in to logout
def logout():
    user_id = get_jwt_identity()


    jti = get_jwt()["jti"]
    redis_client.setex(jti, current_app.config['JWT_ACCESS_TOKEN_EXPIRES'], "true") # Block access token

    # --- Delete cached user data ---
    pipe = redis_client.pipeline()
    pipe.delete(f"user:{user_id}")
    pipe.delete(f"user_solar_system_id:{user_id}") # Delete the mapping


    system_id_str = redis_client.get(f"user_solar_system_id:{user_id}")
    if system_id_str:
        system_id = int(system_id_str)
        pipe.delete(f"solar_system:{system_id}")
        battery_id_str = redis_client.get(f"solar_system_battery_id:{system_id}")
        if battery_id_str:
            battery_id = int(battery_id_str)
            pipe.delete(f"battery:{battery_id}")
            pipe.delete(f"solar_system_battery_id:{system_id}") # Delete the battery mapping too

    pipe.delete(f"user_iot_devices:{user_id}")
    pipe.execute()

    
    response = jsonify({"msg": "Successfully logged out"})
    unset_jwt_cookies(response) 

    return response, 200


