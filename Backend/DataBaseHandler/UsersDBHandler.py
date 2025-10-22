from .DataBaseStart import *
from .IotDBHandler import*
from .BatteryDBHandler import *
from .SolarSystemDBHandler import *

from ..CustomException import *
import bcrypt


def RegisterUser(user:dict) ->dict:
    """
    Registruje novog korisnika u bazu podataka Baca izuzetke u slucaju duplikata username-a/email-a ili problema sa konekcijom.
    Return:
        Vraca registovan user-a kao dict I TAKODJE VRACA njegov ID kreiran u bazi
    """
    #hesiranje sifre cemo u service-u uraditi
    #ovde ce biti exception ako vec postoji User sa ovim username-om

    username             = user["username"]
    email                = user["email"]
    password_hash        = user["password_hash"]
    user_type            = user.get("user_type", "regular")  # podrazumevano 'regular' ako nije prosledjeno
    house_size_sqm       = user["house_size_sqm"]
    num_household_members = user["num_household_members"]
    latitude             = user["latitude"]
    longitude            = user["longitude"]               


    query = """
    INSERT INTO users 
        (username, email, password_hash, user_type, house_size_sqm, num_household_members, latitude, longitude)
    VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    select_query = """
    SELECT * FROM users WHERE user_id = %s
    """
    
    connection = getConnection()

    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, (                         #parametrizovani sql upiti MySql connector insertuje vrednosti u qeurry i provera da li ima SQL injectiona
            username,
            email,
            password_hash,
            user_type,
            house_size_sqm,
            num_household_members,
            latitude,
            longitude
        ))
        connection.commit()
        user_id = cursor.lastrowid

        # da dobijemo 
        cursor.execute(select_query, (user_id,))




        inserted_user = cursor.fetchone()

        inserted_user["house_size_sqm"] = float(inserted_user["house_size_sqm"])
        inserted_user["latitude"] =       float(inserted_user["latitude"])
        inserted_user["longitude"] =      float(inserted_user["longitude"])

        inserted_user["registration_date"]=     inserted_user["registration_date"].timestamp()


        del inserted_user["password_hash"]


        return inserted_user
    
    except mysql.connector.IntegrityError as err:
        connection.rollback()                           #da vratimo bazu u stanje pre nego sto je transakcija pocela, ako postoji duplikat sprecavamo da insertion izvrsi o ostavljamo bazu ne promenjenu
        if err.errno ==1062:
            raise IlegalValuesException("Username/Email already exists")
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while registering the user.") 
    finally:
        cursor.close()
        release_connection(connection)


def GetUserById(user_id:int)->dict:

    query ="""
    SELECT * FROM users WHERE user_id = %s
    """
    connection = getConnection()

    cursor = connection.cursor(dictionary=True)

    try:


        # da dobijemo 
        cursor.execute(query, (user_id,))
        user_db = cursor.fetchone()

        user_db["house_size_sqm"] = float(user_db["house_size_sqm"])
        user_db["latitude"] =       float(user_db["latitude"])
        user_db["longitude"] =      float(user_db["longitude"])
        user_db["registration_date"]=     user_db["registration_date"].timestamp()


        return user_db
    
    except mysql.connector.IntegrityError as err:

        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while registering the user.") 
    finally:
        cursor.close()
        release_connection(connection)


#Fora sa ovim je prilikom logovanja da bi proverili password ne mozemo koristiti onaj hash jel tu ima salt-a i onda
#ce taj salt cak i za dobru unetu sifru je promenuti i nece valjati pa cemo koristiti nes sepcijalno od bcrypt
def GerUserCredentials(userCredentials: dict):

    #ako nije registrovan digni NotFoundException i stavi user not registered 
    query = """
        SELECT user_id, username, email, password_hash, user_type, house_size_sqm, num_household_members, registration_date, latitude, longitude
        FROM users WHERE username = %s;
    """
    #u qeurry proveravamo prvo username dal postoji ako postoji onda izvlacimo hashiranu sifru da proverimo da li je dobra sa unetom sifrom
    username = userCredentials["username"]
    entered_pass= userCredentials["password"]


    connection = getConnection()
    cursor = connection.cursor(dictionary=True)         #ovde ga konvertujemo automatski da vrati kao dict

    try:
        cursor.execute(query,(username,))

        #fetcone vraca kao tuple pa cemo ga konvertovati u dict, lakse je preko dict jer pristupam sa imenima kolona, a ne ono indkesovano 0,1,2,3
        #i jos je JSON ready jer mogu onda direkt da ga vratim direkt ka FLASK-API response preko jsonify
        user = cursor.fetchone()
        if not user:
            raise NotFoundException("Username/password not valid")
        

        #konverzije zato sto Mysql cuva u glupom Decimal(,)
        user["house_size_sqm"] = float(user["house_size_sqm"])
        user["latitude"] =       float(user["latitude"])
        user["longitude"] =      float(user["longitude"])
        user["registration_date"]=     user["registration_date"].timestamp()
        #ovo je izvuceno iz mysql
        db_hashed = user["password_hash"]

        if not bcrypt.checkpw(entered_pass.encode("utf-8"), db_hashed.encode("utf-8")):
            raise NotFoundException("Username/password not valid")

        del user["password_hash"]

        #brisemo da ne bi API response bio presreten ili logovan
        #zbog preksravanja least privlage-a tj frontend ne treba da interesuje sifra


        #vracamo user info
        return user
    
    except mysql.connector.IntegrityError as err:

        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while registering the user.") 
    finally:
        cursor.close()
        release_connection(connection)



def GetAllUsersBasic() -> list[dict]:
    """
    Fetches all users (non-admin and admin) from the database with basic info.
    """
    query = """
    SELECT 
        user_id, username, email, user_type, house_size_sqm, 
        num_household_members, latitude, longitude, registration_date
    FROM users
    WHERE user_type='regular';
    """
    connection = getConnection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query)
        users = cursor.fetchall()

        for user_db in users:
            user_db["house_size_sqm"] = float(user_db["house_size_sqm"])
            user_db["latitude"] = float(user_db["latitude"])
            user_db["longitude"] = float(user_db["longitude"])
            
            if user_db["registration_date"]:
                 user_db["registration_date"] = user_db["registration_date"].timestamp()

        return users
    except mysql.connector.Error as err:
        raise ConnectionException(f"Database error while fetching all users: {str(err)}")
    finally:
        cursor.close()
        release_connection(connection)



def GetAllUsersWithSystemData() -> list[dict]:
    """
    Fetches all users and aggregates their associated solar system, battery, and IoT devices.
    
    Returns:
        list[dict]: A list where each dictionary contains user data and nested system/device data.
    """
    all_users = GetAllUsersBasic()
    

    
    users_with_data = []
    
    for user in all_users:
        user_id = user["user_id"]
        

        # SELECT * FROM solar_systems WHERE user_id = %s
        solar_system = None
        try:
            solar_system = GetSolarSystemByUserId(user_id)
        except Exception: 
            # Catching generic exception here is a common pattern for "optional" related data 
            pass
        
        user["solar_system"] = solar_system
        
        battery = None
        if solar_system and solar_system.get("system_type") == "grid_tied_hybrid":
            try:

                battery = GetBatteryIdBySystemIDService(solar_system["system_id"])
            except Exception:
                pass
        
        if solar_system:
            solar_system["battery"] = battery 


        iot_devices = []
        try:
            iot_devices = GetIoTDevicesByUserId(user_id)
        except Exception:
            pass
            
        user["iot_devices"] = iot_devices
        
        users_with_data.append(user)
        
    return users_with_data



def UpdateUserApprovalStatus(system_id: int, approved: bool) -> None:
    """
    Updates the 'approved' status for a given solar system.
    Args:
        system_id (int): The unique ID of the solar system.
        approved (bool): New approval status (True/False).
    """
    query = """
        UPDATE solar_systems
        SET approved = %s
        WHERE system_id = %s;
    """

    connection = getConnection()
    cursor = connection.cursor()

    try:
        approved_value = 1 if approved else 0
        cursor.execute(query, (approved_value, system_id))

        if cursor.rowcount == 0:
            connection.rollback()
            raise ValueError(f"No solar system found with system_id={system_id}")

        connection.commit()

    except mysql.connector.Error as err:
        connection.rollback()
        raise ConnectionException(f"Database error while updating approval status: {str(err)}")

    finally:
        cursor.close()
        release_connection(connection)


