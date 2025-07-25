from ..Service import *
from flask import Blueprint, request,jsonify,make_response
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt,decode_token,set_access_cookies,set_refresh_cookies,get_csrf_token,get_jwt_identity,unset_jwt_cookies
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
                "user_type": user["user_type"]  
            },
            expires_delta=timedelta(minutes=15) # 20 sekundi za testiranje
        )
        
        refresh_token = create_refresh_token(
            identity=str(user["user_id"]),
            additional_claims={
                "username": user["username"],           
                "user_type": user["user_type"]  # 
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
        pipe.sadd(f"user_tokens:{user['user_id']}", access_jti, refresh_jti)





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
        #ovde treba int posto cemo ici do mysql-a
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
        if not solar_system_data and user_data:                                                 # Samo ako user postoji ovo pokusavamo
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
                "user_id": user_data.get("user_id"),
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
    


@jwt.token_in_blocklist_loader
def check_if_token_is_blacklisted(jwt_header, jwt_payload):     #jwt_header sadrzi metadatu od  tokena, algoritam i type, payload sadrzi decodiran body  JWT sa identitetom i CUSTOM CLAIM-ovima
    jti = jwt_payload["jti"]                                    #jti unique id koji se dodeljuje svakom tokenu prilikom kreatije NIJE isto sto i customClaim
    return redis_client.get(f"blocked_token:{jti}") =="invalid"   #reddis dekodira odma u string jer sam tako stavio u redis clientu




@auth_blueprint.route('/logout',methods=['POST'])
@jwt_required()                              #provera da li je jwt token prisutan u headeru/cookiju,proverava potpis i da li je nesto radjeno sa njim, i provera da nije istekao token
def logout():                                #takoddje raiseuje error ako nema tokena,token je invalid,expired ili revokovan
    try:
        jti= get_jwt()["jti"]
        exp = get_jwt()["exp"]              # da dinamicki postavimo kolko ce u redisu (blacklist) biti token nako sto se logoutuje, postavimo da je timeout trenutno kolko mu je ostalo od original.
        identity = get_jwt_identity()       # vraca id u string formatu

        #NEMA POTREBE DA identity convertujem u int() jer samo radim operacije nad redisom da sam isao do baze podataka onda bi mi trebao int

        

        #VAZNO je namestimo ttl za blacklist da se ne bi desilo da blacklist istekne a token TTL nastavi da postoji onda je presta da bude blacklistovan ! 

        if not jti or not exp:
            return jsonify({"error":"Invalid JWT structure"}),400

        ttl = int(exp - datetime.utcnow().timestamp())
        if ttl < 0:
            ttl=1       #zbog clock skew, imamo sat na serveru i JWT validatora ako slucajn sad kod JWT kasni za 5 sekundi, ako dobijemo negativan ttl da ne bude error u redisu

        pipe = redis_client.pipeline()
        pipe.multi()

        #pri logout-u usera blaclistujemo njegov accsess token i refresh token, bolje je blacklistovanj-e nego da ih brisem u access_token i refresh_token  reddis-u
        # jer bi bilo onda inconsistency ako konkrutetno app pokusa da refresh-uje i validatuje tokene, JWT_required ce izbeci race conditione jel prvo provera blacklist pa tek dozvoljava funk da se izvrsi


        pipe.setex(f"blocked_token:{jti}", ttl, "invalid")      #dodamo expiration
 
        #iz seta aktivnih access tokena brisemo acsess tokena od trenutne sesije user-a koja se odjavljuje
        pipe.srem(f"user_tokens:{identity}", jti)

        #blacklistovanje REFRESH tokena


        # Uzmemo refresh token iz cookie-a, ovo je bio prethodni problem sa logout-om jer sam preko ovog verift_jwt_in_request...
        # ali ga necu verifikovati preko verify_jwt_in_request(refresh=True)
        # jer @jwt_required() iznad vec brine o autenticnosti
        # Njegova validacija ce se desiti u okviru pipe.setex ako je prisutan
        refresh_token_cookie_value = request.cookies.get('refresh_token_cookie')

        if refresh_token_cookie_value: # provera da li postoji uopste refresh_token
            try:
                # Dekodiramo refresh token (Flask-JWT-Extended ovo radi sigurno proverava potpis)
                # Nema potrebe za 'verify_jwt_in_request' ovde jer je cilj samo blacklistovanje
                # a ne autorizacija pristupa ruti
                decoded_refresh = decode_token(refresh_token_cookie_value)
                refresh_jti = decoded_refresh["jti"]
                refresh_exp = decoded_refresh["exp"]

                ttl_refresh = int(refresh_exp - datetime.utcnow().timestamp())
                if ttl_refresh < 0:
                    ttl_refresh = 1 # Minimalni TTL

                pipe.setex(f"blocked_token:{refresh_jti}", ttl_refresh, "invalid")
                pipe.srem(f"user_tokens:{identity}", refresh_jti) # Ukloni JTI refresh tokena iz seta korisnika
            except Exception as e:
                # Loguj grešku ako dekodiranje refresh tokena ne uspe (npr. istekao je ranije, tampered)
                print(f"Error decoding or blacklisting refresh token during logout: {e}")
                # Nastavi dalje, jer je glavni cilj logouta postignut (access token je blacklistovan)


        # Brisanje cache-a da bi pri login-u dobili fresh data
        # Brisemo iot
        pipe.delete(f"user:{identity}")
        pipe.delete(f"user_iot_devices:{identity}")

        # 
        # odavde izvucemo solar_system id
        solar_system_id_str = redis_client.get(f"user_solar_system_id:{identity}")
        if solar_system_id_str:
            solar_system_id = int(solar_system_id_str)                                          #nije moralo da se konvertuje
            pipe.delete(f"solar_system:{solar_system_id}")
            # ako postoji baterija, brisemo i njen cache
            battery_id_str = redis_client.get(f"solar_system_battery_id:{solar_system_id}")
            if battery_id_str:
                battery_id = int(battery_id_str)
                pipe.delete(f"battery:{battery_id}")
                pipe.delete(f"solar_system_battery_id:{solar_system_id}") 
            pipe.delete(f"user_solar_system_id:{identity}") 

        #izvrsavamo reddis komande atomicno
        pipe.execute()      


        response = make_response(jsonify({"message": "Logged out successfully"}), 200)
        unset_jwt_cookies(response)  #OVO JE NAJBITNIJE 
                                     #Ovo šalje instrukcije browser-u da obriše
                                     # HttpOnly kolačiće (access_token_cookie, refresh_token_cookie, csrf_access_token, csrf_refresh_token)

        # brisemo i refresh zato sto: Ostavljanje refresh cookie znaci da client moze da zatrazi novi acces cookie token silently preko POST /refresh
        # ako se ne obrise onda: client moze da refresh-uje silently, sto onda ponistava logging out

        #Ovo je kad admin banuje user-a ili sa LOGOUT out of everything
        # for jti in redis_client.smembers(f"user_tokens:{identity}"):
        #    redis_client.setex(f"blocked_token:{jti.decode()}", 7 * 24 * 3600, "invalid")  # 7 days
        #redis_client.delete(f"user_tokens:{identity}")


        return response
    
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except Exception as e:
        return jsonify({"error":str(e)}), 500
    

# Kada user-u istekne access token dobice od server not authorized i onda ce axios interceptor probati da refreshuje access token user-a
# Ovde nema potrebe za cachiranjem podataka user-a,solar system,iot itd.. za to ce biti /me zaduzen
@auth_blueprint.route('/refresh',methods=['POST'])
@jwt_required(refresh=True)             #zahteva validan REFRESH token da bi se pristupilo ovoj funkciji
def refresh():
    try:

        #uzima od refresh jwt-a INFO, zato sto samo cookie sa refresh tokenom moze da pristupi ovoj funkciji zbog refresh=True
        #ne moram da unpackujem jwt token in cooki-a to se automatski uradi sa get_jtw_identity

        identity = get_jwt_identity()   # id user-a
        claims = get_jwt()              # ceo JWT REFRESH TOKEN-a payload ukljucujuci "jti", "exp", "user_type", etc.

        #potrebno je u reddisu invalidatovati stari token i dodati ovaj novi
        old_refresh_jti  = claims.get("jti")         #unique token id za revocation je koristan

        #Blacklistujemo stari refresh i stari access token, i radimo refresh token rotation tj izdajemo novi refresh token

        # "In JWT-based authentication, tokens are self-contained — meaning they don’t require server-side sessions to validate them. But this also means:
        #  If a token hasn’t expired, it’s technically still valid even if the user logs out or it’s supposed to be blocked — unless you track and reject it manually".
        
        pipe = redis_client.pipeline()

        old_access_token = request.cookies.get("access_token_cookie")  #Blacklistujemo stari ACCESS token kog vadimo iz cookie-a, default ime
        if old_access_token:                                            
            try:
                decoded_old_access = decode_token(old_access_token)    #decode_token ce biti dovoljno siguran zato sto se prenosi preko HTTP samo i CSFR secure je
                old_access_jti = decoded_old_access["jti"]

                pipe.setex(f"blocked_token:{old_access_jti}",int(timedelta(minutes=30).total_seconds()),"invalid"
                )
            except Exception as err:
                print(f"Old access token decode failed: {err}")
                pass  # Istekli or malformed token – ignorisemo

         # Blacklistujemo the old refresh token (opcionalno ali bolja sigurnost)
        pipe.setex(f"blocked_token:{old_refresh_jti}",int(timedelta(days=7).total_seconds()),"invalid")       
        
        

        # pravimo novi acsess token

        new_access_token = create_access_token(
            identity=identity,
            additional_claims={
                "username": claims.get("username", ""),           
                "global_admin": claims.get("global_admin")    
            },
            expires_delta=timedelta(minutes=15) 
        )
        #novi refresh token pravimo
        new_refresh_token = create_refresh_token(
            identity=identity,
            additional_claims={
                "username": claims.get("username", ""),           
                "global_admin": claims.get("global_admin")   
            },
            expires_delta=timedelta(days=7) 
        )


        decoded_new_access  = decode_token(new_access_token)
        decoded_new_refresh = decode_token(new_refresh_token)

        new_jti_access = decoded_new_access["jti"]
        new_jti_refresh = decoded_new_refresh["jti"]

        # Metadata user-a
        user_metadata_access = {
            "user_id": identity,
            "username": claims.get("username", ""),  # optional: fetch again if needed
            "user_type": claims.get("user_type"),
            "status": "valid",
            "issued_at": decoded_new_access["iat"],
            "expires": decoded_new_access["exp"]
        }

        user_metadata_refresh = {
            "user_id": identity,
            "username": claims.get("username", ""),  # optional: fetch again if needed
            "user_type": claims.get("user_type"),
            "status": "valid",
            "issued_at": decoded_new_refresh["iat"],
            "expires": decoded_new_refresh["exp"]
        }

        # Store new access token by JTI
        pipe.setex(f"access_token:{new_jti_access}",int(timedelta(minutes=15).total_seconds()),json.dumps(user_metadata_access))
        pipe.setex(f"refresh_token:{new_jti_refresh}",int(timedelta(days=7).total_seconds()),json.dumps(user_metadata_refresh))
    

        # dodajemo u set id usera njegov jti
        pipe.sadd(f"user_tokens:{identity}", new_jti_access, new_jti_refresh)


        #executujemo sve reddis komande atomicno 
        pipe.execute()

        #novi accses stavljamo u secure cookie
        response = make_response(jsonify({"message": "Access token refreshed"}))
        set_access_cookies(response, new_access_token)
        set_refresh_cookies(response,new_refresh_token)



        
        return response
    
    #mora pre genericno exception-a ovaj redis exception
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except Exception as e:
        return jsonify({"error": str(e)}), 500