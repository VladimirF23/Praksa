from .DataBaseStart import *
from ..CustomException import *


def RegisterBattery(battery: dict) -> dict:
    """
    Tok ce ici ovako Prvo se kreira user onda proverimo u API-u u solar_system-u da li je gridTied-Hybrid ako jeste onda kreiramo bateriju i vracamo njen ID posto se on mora proslediti 
    solar_systemu jer ima foreign key na battery id 
    Zbog relaksiranosti min kardinaliteta izmedju Battery i SolarConfiga ostavicemo u battery tabeli za trenutno battery solad_id NULL i dodacemo ga odma posle kreiranja solar_system-a koji ima ovu bateriju

    OBAVEZNO se posle kreiranja solar_system-a mora uzeti njegov id i proslediti battery-u 


    Registujemo novu bateriju u Bazi podataka.
    Return-uje ID novo kreirane baterije
    Raise-uje Exception-e za duplikate system_id ili connection issues.
    """
    system_id = battery.get("system_id")                # na pocetku ce biti NULL
    model_name = battery.get("model_name")
    capacity_kwh = battery["capacity_kwh"]                          # Ovo NE SME da bude NULL,  KeyError exception se raise-uje ako fali
    max_charge_rate_kw = battery.get("max_charge_rate_kw")
    max_discharge_rate_kw = battery.get("max_discharge_rate_kw")
    efficiency = battery.get("efficiency")
    manufacturer = battery.get("manufacturer")
    current_charge_percentage = battery.get("current_charge_percentage") # Neku default vrednost cu uneti

    query = """
    INSERT INTO batteries
        (system_id, model_name, capacity_kwh, max_charge_rate_kw,
         max_discharge_rate_kw, efficiency, manufacturer, current_charge_percentage)
    VALUES
        (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    select_query = "SELECT * FROM batteries WHERE battery_id = %s"

    connection = None
    cursor = None
    try:
        connection = getConnection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(query, (
            system_id,
            model_name,
            capacity_kwh,
            max_charge_rate_kw,
            max_discharge_rate_kw,
            efficiency,
            manufacturer,
            current_charge_percentage
        ))

        connection.commit()

        new_battery_id = cursor.lastrowid

        # SELECT newly inserted battery as dict
        cursor.execute(select_query, (new_battery_id,))
        inserted_battery = cursor.fetchone()

        inserted_battery["capacity_kwh"] =               float(inserted_battery["capacity_kwh"])
        inserted_battery["max_charge_rate_kw"] =         float(inserted_battery["max_charge_rate_kw"])
        inserted_battery["max_discharge_rate_kw"] =      float(inserted_battery["max_discharge_rate_kw"])
        inserted_battery["efficiency"] =                 float(inserted_battery["efficiency"])
        inserted_battery["current_charge_percentage"] =  float(inserted_battery["current_charge_percentage"])

        return inserted_battery                           #vratimo celu bateriju kao dict 

    except mysql.connector.IntegrityError as err:
        if connection:
            connection.rollback()
        if err.errno == 1062:
            raise IlegalValuesException("A battery for this solar system already exists or a duplicate entry was attempted.")
        elif err.errno == 1406:
            raise IlegalValuesException("The provided battery values are in an invalid format or too long.")
        else:
            raise DuplicateKeyException(f"Database integrity error: {err}")
    except KeyError as e:
        raise IlegalValuesException(f"Missing required battery field: {e}. Please ensure 'capacity_kwh' is provided.")
    except Exception as e:
        raise ConnectionException(f"An unexpected error occurred during battery registration: {e}")
    finally:
        cursor.close()
        release_connection(connection)


def AddSolarSystemToBattery(battery_id, system_id) -> bool:
    """
    Nakon kreiranja solarnog system-a u zavisnosti od toga da li je hibridni dodajemo bateirji id solarnog sistema kom ona pripada
    Zbog UNIQUE constraint-a na 'solar_system_id' u tabeli 'batteries',
    jedan solarni sistem moze biti povezan sa najviše jednom baterijom.

    Args:
        battery_id (int): ID baterije koju treba azurirati.
        solar_system_id (int): ID solarnog sistema koji treba povezati sa baterijom.

    Returns:
        bool: True ako je azuriranje uspešno, False ako ne

    Raises:
        IlegalValuesException: Ako dode do problema sa integritetom baze podataka (npr.
                               pokusaj povezivanja istog solarnog sistema sa vise baterija,
                               ili nevalidni ID-evi, ili baterija nije pronadjena).
        ConnectionException: Ako dodje do problema sa povezivanjem na bazu podataka.
    """

    query = """
    UPDATE batteries SET system_id =%s
    WHERE battery_id =%s;
    """
    connection = None
    cursor = None
    try:
        connection = getConnection() 
        cursor = connection.cursor()

        cursor.execute(query, (system_id, battery_id))

        # Proveravamo da li je neka baterija zaista updejtovana
        # Ako battery_id ne postoji, affected_rows će biti 0.
        if cursor.rowcount == 0:
            if connection:
                connection.rollback()           #ponistavamo promene pre raise-ovanja exception-a

        connection.commit()
        print(f"Baterija ID {battery_id} uspešno povezana sa solarnim sistemom ID {system_id}.")
        return True

    except mysql.connector.IntegrityError as err:
        if connection:
            connection.rollback()
        
        if err.errno == 1062:                                           
            raise DuplicateKeyException(
                f"Solar System ID: {system_id} is already connected to another battery"
                "One solar system suports one battery"
            )
        # MySQL greska za strani kljuc koji ne postoji (ako solar_system_id ne postoji u solar_systems tabeli)
        elif err.errno == 1452: # Foreign key constraint fails
            raise IlegalValuesException(
                f"Solar System with ID: {system_id} doesn't exist"
            )
    except Exception as e:
        raise ConnectionException(f"Unexpected erorr with connection with DataBase while updating batteries solar system id,  {e}")
    finally:
        cursor.close()
        release_connection(connection) 


def GetBatteryData(battery_id: int) ->dict:
    query ="""
    SELECT * FROM batteries WHERE battery_id = %s
    """
    connection = getConnection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, (battery_id,))
        battery = cursor.fetchone()

        battery["capacity_kwh"] =               float(battery["capacity_kwh"])
        battery["max_charge_rate_kw"] =         float(battery["max_charge_rate_kw"])
        battery["max_discharge_rate_kw"] =      float(battery["max_discharge_rate_kw"])
        battery["efficiency"] =                 float(battery["efficiency"])
        battery["current_charge_percentage"] =  float(battery["current_charge_percentage"])



        return battery

    except mysql.connector.Error as err: # Catch generic MySQL errors for robustness
        connection.rollback()

        raise ConnectionException(f"Database error occurred while fetching battery: {str(err)}")
    finally:
        cursor.close()
        release_connection(connection)

def GetBatteryIdBySystemIDService(system_id:int)->dict:
    query ="""
    SELECT * FROM batteries WHERE system_id = %s
    """
    connection = getConnection()

    cursor = connection.cursor(dictionary=True)

    try:


        # da dobijemo 
        cursor.execute(query, (system_id,))
        battery = cursor.fetchone()

        battery["capacity_kwh"] = float(battery["capacity_kwh"])
        battery["max_charge_rate_kw"] = float(battery["max_charge_rate_kw"])
        battery["max_discharge_rate_kw"] = float(battery["max_discharge_rate_kw"])
        battery["efficiency"] = float(battery["efficiency"])
        battery["current_charge_percentage"] = float(battery["current_charge_percentage"])

        return battery
    
    except mysql.connector.IntegrityError as err:
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while registering the user.") 
    finally:
        cursor.close()
        release_connection(connection) 
