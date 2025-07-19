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
        solar_system_db = RegisterSolarSystem(solar_system_data, user_db["user_id"],battery_id)
        


        
        #ovde se mora updejtovati ako postoji baterija
        if battery_db:
            AddSolarSystemToBatteryService(battery_id,solar_system_data["system_id"])

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
            identity=str(user["id"]),                                               #postavlje se id (broj) user-a za jedinstveni broj access_token-a zato sto se id nikad nece menjati a username se moze menjati
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