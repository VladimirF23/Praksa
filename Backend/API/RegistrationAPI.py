from ..Service import *
from flask import Blueprint, request,jsonify,make_response
from ..CustomException import *
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt,decode_token,set_access_cookies,set_refresh_cookies,get_csrf_token
from datetime import timedelta,datetime
from extensions import jwt,redis_client
from decimal import Decimal 


import redis

#Check Redis connection on app startup
try:
    redis_client.ping()  # Test Redis connection
except redis.ConnectionError:
    raise Exception("Failed to connect to Redis.")

def calculate_base_consumption(house_size_m2, household_members):
    # Osnovna logika (moze se prilagoditi)
    return (house_size_m2 * 0.05) + (household_members * 1.5)

#metoda je post jer POST drzi sensitive data (email/password) u request body a on nije logovan u browser history
registration_blueprint = Blueprint('registration',__name__,url_prefix='/registration')


@registration_blueprint.route('', methods =['POST'])
def register_user():
    """
        Sa Front-a Dobijemo podatke vezane za user-a -> koji idu u user's table
        Vazan je redosled ubacivanja u bazu podataka prvo trebamo user-a, bateriju ili iot(posto zavise od user-a), solar configuaricju (posto moze izabrati user odredjenu bateriju)

        Napravimo prvo user-a
        Napravimo bateriju ako je to opciju izabrao napravimo bateriju (ako user je stavio gried tied nece imati bateriju TAKO DA U FRONT-u MU NE DOZVOLITI DA IZABERE BATERIJU)

        Napravimo Solar sistem, posto on zavisi od user-a i baterije
        Dodamo ID solar sistema u tabelu baterije

        Ako je user dodao IoT uredjaje napravimo ih i prosledimo im id user-a i id solarnog sistema

        DODAJ OVDE EXCEPTIONE TAKO DA POKRIJU SVE EXCEPTIONE DB SLOJA I SERVICE SLOJA
        Treba preko exception-a vracati greske ne treba na osnovu True/False ili id zato sto sam vec dodao htpp codove koji ce se vracati za odredjene exceptione !!!
        
    """
    try:
        data =request.get_json()

        #username,email,password
        if not data:
            return jsonify({"error":"Invalid JSON format"}),400
        

        user_data = {
        "username": data.get("username"),
        "email": data.get("email"),
        "password": data.get("password"),               # hashiramo kasnije
        "user_type": data.get("user_type", "regular"),  # Default if missing
        "house_size_sqm": data.get("house_size_sqm"),
        "num_household_members": data.get("num_household_members"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude")
        }
        


        #pitaj chat gpt da li je moguce posto ovde imamo proveru, da nekako user pogodi one metode u Engine layeru i onda da zato moramo da imamo provere na vise layer-a
        required_fields =["username", "email", "password","house_size_sqm","latitude","longitude"]
        missing_fields =[field for field in required_fields if field not in user_data]

        if missing_fields:
            return jsonify({"error":f"Missing fields: {', '.join(missing_fields)}"}),400

        #service layer zovemo
        user_db = RegisterUserService(user_data)


        #BATERIJA JE OPCIONALNA !!!
        battery_fields = [
        "model_name", "capacity_kwh", "max_charge_rate_kw",
        "max_discharge_rate_kw", "efficiency", "manufacturer", "current_charge_percentage"
        ]

        battery_data_present = any(field in data for field in battery_fields)

        battery_db = None  # Default, Nema baterije
        
        if battery_data_present:

        #napravimo bateriju ciji cemo id poslati solar sistemu
            battery_data = {
            "system_id": data.get("system_id"),  # Can be None if not yet created
            "model_name": data.get("model_name"),
            "capacity_kwh": data.get("capacity_kwh"),
            "max_charge_rate_kw": data.get("max_charge_rate_kw"),
            "max_discharge_rate_kw": data.get("max_discharge_rate_kw"),
            "efficiency": data.get("efficiency"),
            "manufacturer": data.get("manufacturer"),
            "current_charge_percentage": data.get("current_charge_percentage", 0.00)  # Default if missing
            }

        # Proverimo da li fale neka polja ako postoji baterija
            required_fields_battery = battery_fields[:-1]  # Exclude current_charge_percentage from required
            missing_fields_battery = [field for field in required_fields_battery if not data.get(field)]

            if missing_fields_battery:
                return jsonify({"error": f"Missing fields for battery: {', '.join(missing_fields_battery)}"}), 400

            #saljemo ka service-u battery_data, ako se uspesno doda u bazu podata vraca nam bateriju u obliku dictionary
            battery_db = RegisterBatteryService(battery_data)
            battery_id = battery_db["battery_id"]
        else:
            battery_id = None


        #pravimo sad solar sistem, POSALJI ID user[id] koji je kreiran u bazi

        

        base_consumption_kwh =calculate_base_consumption(user_db["house_size_sqm"], user_db["num_household_members"])

        solar_system_data = {
        "system_name": data.get("system_name"),
        "system_type": data.get("system_type"),  # must be 'grid_tied' or 'grid_tied_hybrid'
        "total_panel_wattage_wp": data.get("total_panel_wattage_wp"),
        "inverter_capacity_kw": data.get("inverter_capacity_kw"),
        "base_consumption_kwh": base_consumption_kwh
        }


        #dodajemo user_id i battery_id moze biti None
        solar_system_db = RegisterSolarSystemService(solar_system_data, user_db["user_id"],battery_id)
        


        
        #ovde se mora updejtovati ako postoji baterija
        if battery_db:
            AddSolarSystemToBatteryService(battery_id,solar_system_db["system_id"])

            #ovde takodje zbog cache-a posle
            battery_db["system_id"] = solar_system_db["system_id"]

        
            # IOT stuff
            # bice u jsonu kao lista njih
        #       "iot_devices": [
        #   {
        #   "device_name": "Klima",
        #   "device_type": "AC",
        #   "base_consumption_watts": 2200,
        #   "priority_level": "medium",
        #   "current_status": "off",
        #   "is_smart_device": true
        #   },
        #   {
        #   "device_name": "Bojler",
        #   "device_type": "Water Heater",
        #   "base_consumption_watts": 1500,
        #   "priority_level": "non_essential",
        #   "current_status": "off",
        #   "is_smart_device": false
        #   }
        # ]
        iot_devices_data = data.get("iot_devices")

        #opcionalni su ne moraju da postoje
        if iot_devices_data:
            RegisterIoTService(iot_devices_data, user_db["user_id"], solar_system_db["system_id"])
            iot_devices_db = GetUsersIOTsService(user_db["user_id"])            #ovo je lista dictionari-a

        #treba nam njihov id 

        access_token = create_access_token(
            identity=str(user_db["user_id"]),                                               #postavlje se id (broj) user-a za jedinstveni broj access_token-a zato sto se id nikad nece menjati a username se moze menjati
            additional_claims={
                "username": user_db["username"],           
                "user_type": user_db["user_type"]  # Changed from "global_admin"
            },
            expires_delta=timedelta(minutes=15) # 20 sekundi za testiranje
        )
        
        refresh_token = create_refresh_token(
            identity=str(user_db["user_id"]),
            additional_claims={
                "username": user_db["username"],           
                "user_type": user_db["user_type"]  # Changed from "global_admin"
            },
            expires_delta=timedelta(days=7) 
        )

        decoded_access  = decode_token(access_token)
        decoded_refresh = decode_token(refresh_token)

        access_jti  = decoded_access["jti"]
        refresh_jti = decoded_refresh["jti"]


        # ove metapodatke mogu koristiti u buducnosti ako admin banuje nekog user-a da tamo u authentification-u proverimo da li je valid i ako nije cancelujemo mu sve access/refresh tokene preko set-a kog sam dole napravio
        # na foru ove funkcije  @jwt.token_in_blocklist_loader def check_if_token_is_blacklisted(jwt_header, jwt_payload):
        # al to tek kasnije 
        user_metadata_access = {
            "user_id": user_db["user_id"], 
            "username": user_db["username"],
            "user_type": user_db["user_type"], 
            "status": "valid",                      # Kljucno za revokaciju
            "issued_at": decoded_access["iat"],  # epoch
            "expires": decoded_access["exp"],    # epoch
            "type" : "access_token"
        }
        user_metadata_refresh = {
            "user_id": user_db["user_id"], 
            "username": user_db["username"], 
            "user_type": user_db["user_type"], 
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
        pipe.sadd(f"user_tokens:{user_db['user_id']}", access_jti, refresh_jti)

        #npr alice je logovan-a sa 2 razlicita device-a (ili sesije) svaka sesija dobija access token i refresh token, (nisam refresh napisao)
        #  Redis Key	                  Stored Value (simplified JSON)	                                                TTL
        #access_token:abc123	{ "user_id": "1", "username": "alice", "type": "access_token", ... }	                15 minutes
        #access_token:ghi789	{ "user_id": "1", "username": "alice", "type": "access_token", ... }                    15 minutes
        #refresh_token:xyz456    { "user_id": "1", "username": "alice", "type": "refresh_token", "status": "valid" ... }  7 days
        #refresh_token:uvw012    { "user_id": "1", "username": "alice", "type": "refresh_token", "status": "valid" ... }  7 days
        # SET user_tokens
        #              ID                             #JTI 
        #user_tokens:   1           {"abc123", "ghi789", "xyz456", "uvw012"} // Redis SET za user-a sa  ID-om 1


        user_id = user_db["user_id"]

        #2. Cachiranje user-a
        user_cache_data = {
            "user_id": user_id,
            "username": user_db["username"],
            "email": user_db["email"],
            "user_type": user_db["user_type"],
            "house_size_sqm": user_db["house_size_sqm"],
            "num_household_members": user_db["num_household_members"],
            "latitude": user_db["latitude"],
            "longitude": user_db["longitude"],
            "registration_date": user_db["registration_date"],              #bice u fomratu tipa 1753104047.0 sto je validno posto ovo moze da se json dumpuje u redis, govori kolko vremena je proslo od 1970 ....
            "last_cached_at": datetime.now().timestamp()                        
        }
        # TTL za user podatke, 1 sat (3600 seconds)
        pipe.setex(f"user:{user_id}", 3600, json.dumps(user_cache_data))

        solar_system_id = solar_system_db["system_id"]

        # 3. Cache Solar System Data
        solar_system_cache_data = {
            "system_id": solar_system_id,
            "user_id": user_id,
            "battery_id": battery_id, # Can be None
            "system_name": solar_system_db["system_name"],
            "system_type": solar_system_db["system_type"],
            "total_panel_wattage_wp": solar_system_db["total_panel_wattage_wp"],
            "inverter_capacity_kw": solar_system_db["inverter_capacity_kw"],
            "base_consumption_kwh": solar_system_db["base_consumption_kwh"],
            "last_cached_at": datetime.now().timestamp()
        }

        # TTL za solar system data, 1 hour (3600 seconds)
        pipe.setex(f"solar_system:{solar_system_id}", 3600, json.dumps(solar_system_cache_data))
        pipe.set(f"user_solar_system_id:{user_id}", str(solar_system_id))                       # da bih posle mogao pre user_id da dobavim system_id od solarnog sistema


        # 4. Cache Battery Data (ako postoji)
        if battery_db:
            battery_cache_data = {
                "battery_id": battery_id,
                "system_id": battery_db["system_id"], 
                "model_name": battery_db["model_name"],
                "capacity_kwh": battery_db["capacity_kwh"],
                "max_charge_rate_kw": battery_db["max_charge_rate_kw"],
                "max_discharge_rate_kw": battery_db["max_discharge_rate_kw"],
                "efficiency": battery_db["efficiency"],
                "manufacturer": battery_db["manufacturer"],
                "current_charge_percentage": battery_db["current_charge_percentage"],
                "last_cached_at": datetime.now().timestamp()
            }
            # TTL za battery data, 30 minutes (1800 seconds)
            pipe.setex(f"battery:{battery_id}", 1800, json.dumps(battery_cache_data))
            pipe.set(f"solar_system_battery_id:{solar_system_id}", str(battery_id))                       # da bih preko system_id mogao da dobavim podatke o bateriji

        # 5. Cache IoT Devices Data (ako postoje)
        if iot_devices_data:
            # Cache  cele liste IoT devices od user-a
            # Posle pogledaj da li treba individualno cachiranje IoT device-a
            iot_devices_list_cache = {
                "user_id": user_id,
                "solar_system_id": solar_system_id,
                "devices": iot_devices_db,                      # lista dictionary-a
                "last_cached_at": datetime.now().timestamp()
            }
            # TTL for IoT devices, maybe shorter, e.g., 5-15 minutes (300-900 seconds)
            pipe.setex(f"user_iot_devices:{user_id}", 600, json.dumps(iot_devices_list_cache))


        pipe.execute()

        #novi accses stavljamo u secure cookie
        response = make_response(jsonify({"message": "User Registered in successfully"}))
        set_access_cookies(response, access_token)
        set_refresh_cookies(response,refresh_token)


        # CSRF token se GENERISAO VEC zasebno u JWT tokenu jer smo stavili JWT_COOKIE_CSRF_PROTECT = True
       

        return response,201

    except IlegalValuesException  as e:
        return jsonify({"error":str(e)}), 400
    except redis.RedisError as e:
        return jsonify({"error":"Redis error","details":str(e)}),500
    except DuplicateKeyException as e:
        return jsonify({"error":str(e)}), 400
    except ConnectionException as e:
        return jsonify({"error":str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error", "details": str(e)}),500