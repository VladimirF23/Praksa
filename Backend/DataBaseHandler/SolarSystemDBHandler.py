from .DataBaseStart import *
from ..CustomException import *




def RegisterSolarSystem(solar_system:dict,user_id:int, battery_id:int) -> int:
    """
        Registrujemo Solarni System on ima Foreign key-eve: user_id i battery_id, battery_id je relaksiran i moze da bude null
        tj u slucaju kada sistme nije gridTiedHybrid battery ce biti null


    
    """

    system_name             = solar_system["system_name"]
    system_type             = solar_system["system_type"]  # 'grid_tied' ili 'grid_tied_hybrid'
    total_panel_wattage_wp  = solar_system["total_panel_wattage_wp"]
    inverter_capacity_kw    = solar_system["inverter_capacity_kw"]

    exception_messages = []

    if not system_name:
        exception_messages.append("System name can't be NULL.")
    if not system_type:
        exception_messages.append("System type can't be NULL.")
    if not total_panel_wattage_wp:
        exception_messages.append("Total panel wattage can't be NULL.")
    if not inverter_capacity_kw:
        exception_messages.append("Inverter capacity can't be NULL.")
    if exception_messages:
        raise IlegalValuesException(" ".join(exception_messages))


    query = """
    INSERT INTO solar_systems 
        (user_id, system_name, system_type, total_panel_wattage_wp, inverter_capacity_kw, battery_id)
    VALUES 
        (%s, %s, %s, %s, %s, %s)
    """

    connection = getConnection()
    cursor = connection.cursor()

    try:
        cursor.execute(query, (
            user_id,
            system_name,
            system_type,
            total_panel_wattage_wp,
            inverter_capacity_kw,
            battery_id  # moze biti None → NULL u bazi
        ))
        connection.commit()
        return cursor.lastrowid                 #vracamo id solar systema da bi mogli da ga damo bateriji

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



