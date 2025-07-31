from .DataBaseStart import *
from ..CustomException import *




def RegisterSolarSystem(solar_system:dict,user_id:int, battery_id:int) -> dict:
    """
        Registrujemo Solarni System on ima Foreign key-eve: user_id i battery_id, battery_id je relaksiran i moze da bude null
        tj u slucaju kada sistme nije gridTiedHybrid battery ce biti null


    
    """

    system_name             = solar_system["system_name"]
    system_type             = solar_system["system_type"]  # 'grid_tied' ili 'grid_tied_hybrid'
    total_panel_wattage_wp  = solar_system["total_panel_wattage_wp"]
    inverter_capacity_kw    = solar_system["inverter_capacity_kw"]
    base_consumption_kw     = solar_system["base_consumption_kw"]

    azimuth_degrees         = solar_system["azimuth_degrees"]
    tilt_degrees            = solar_system["tilt_degrees"]

    exception_messages = []

    if not system_name:
        exception_messages.append("System name can't be NULL.")
    if not system_type:
        exception_messages.append("System type can't be NULL.")
    if not total_panel_wattage_wp:
        exception_messages.append("Total panel wattage can't be NULL.")
    if not inverter_capacity_kw:
        exception_messages.append("Inverter capacity can't be NULL.")
    if not base_consumption_kw:
        exception_messages.append("Base consumption can't be NULL.")
    if not azimuth_degrees:
        exception_messages.append("Azimuth degrees can't be NULL.")
    if not tilt_degrees:
        exception_messages.append("Tilt degrees can't be NULL.")


    if exception_messages:
        raise IlegalValuesException(" ".join(exception_messages))


    query = """
    INSERT INTO solar_systems 
        (user_id, system_name, system_type, total_panel_wattage_wp, inverter_capacity_kw, battery_id,base_consumption_kw,azimuth_degrees,tilt_degrees)
    VALUES 
        (%s, %s, %s, %s, %s, %s,%s,%s,%s)
    """

    select_query="""
    SELECT *  FROM solar_systems where system_id=%s
    """

    connection = getConnection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, (
            user_id,
            system_name,
            system_type,
            total_panel_wattage_wp,
            inverter_capacity_kw,
            battery_id,  # moze biti None → NULL u bazi
            base_consumption_kw,
            azimuth_degrees,
            tilt_degrees
        ))
        connection.commit()

        system_id = cursor.lastrowid

        # da dobijemo 
        cursor.execute(select_query, (system_id,))
        inserted_solarSystem = cursor.fetchone()

        #da bi moglo u redisu da se jsondumpuje zbog glupavog Decimal u Mysql...
        inserted_solarSystem["total_panel_wattage_wp"] = float(inserted_solarSystem["total_panel_wattage_wp"])
        inserted_solarSystem["inverter_capacity_kw"] = float(inserted_solarSystem["inverter_capacity_kw"])
        inserted_solarSystem["base_consumption_kw"] = float(inserted_solarSystem["base_consumption_kw"])

        return inserted_solarSystem                 

    except mysql.connector.IntegrityError as err:
        connection.rollback()
        if err.errno == 1062:
            raise IlegalValuesException("User already has a registered solar system.")
        if err.errno == 1452:
            raise IlegalValuesException("Invalid user_id or battery_id (foreign key violation).")
        if err.errno == 1406:
            raise IlegalValuesException("A value is too long or improperly formatted.")
        raise

    except mysql.connector.OperationalError:
        connection.rollback()
        raise ConnectionException("A database connection error occurred while registering the solar system.")
    
    finally:
        cursor.close()
        release_connection(connection)



def GetSolarSystemByUserId(user_id:int)->dict:
    query ="""
    SELECT * FROM solar_systems WHERE user_id = %s
    """
    connection = getConnection()

    cursor = connection.cursor(dictionary=True)

    try:


        # da dobijemo 
        cursor.execute(query, (user_id,))
        solar_system = cursor.fetchone()

        solar_system["total_panel_wattage_wp"] = float(solar_system["total_panel_wattage_wp"])
        solar_system["inverter_capacity_kw"] = float(solar_system["inverter_capacity_kw"])
        solar_system["base_consumption_kw"] = float(solar_system["base_consumption_kw"])


        
        return solar_system
    
    except mysql.connector.IntegrityError as err:
        if err.errno ==1406:
            raise IlegalValuesException("The values are in invalid fromat")
        
    except mysql.connector.OperationalError:
        connection.rollback()  
        raise ConnectionException("An connection error occurred while registering the user.") 
    finally:
        cursor.close()
        release_connection(connection) 




