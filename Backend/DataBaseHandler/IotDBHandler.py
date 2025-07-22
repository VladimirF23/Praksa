from .DataBaseStart import *
from ..CustomException import *



#vraca samo True za ostalo se exceptioni pobrinu
# BATCH Inserion radimo
def RegisterIoTDevices(iot_devices: list[dict], user_id: int, system_id: int) -> bool:
    """
    Registruje vise IoT uredjaja odjednom Povezuje uredjaje sa korisnikom i (opcionalno) sa solarnim sistemom

    solart_system_id == system_id
    """

    query = """
    INSERT INTO iot_devices 
        (user_id, system_id, device_name, device_type, base_consumption_watts,
         priority_level, current_status, is_smart_device)
    VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values_to_insert = []
    for device in iot_devices:
        values_to_insert.append((
            user_id,
            system_id if system_id else None,
            device["device_name"],
            device["device_type"],
            device["base_consumption_watts"],
            device["priority_level"],
            device["current_status"],
            device["is_smart_device"]
        ))

    connection = getConnection()
    cursor = connection.cursor()

    try:
        cursor.executemany(query, values_to_insert)
        connection.commit()
        return True

    except mysql.connector.IntegrityError as err:
        connection.rollback()
        if err.errno == 1452:
            raise IlegalValuesException("Invalid user_id or system_id (foreign key violation).")
        if err.errno == 1406:
            raise IlegalValuesException("A value is too long or improperly formatted.")
        raise

    except mysql.connector.OperationalError:
        connection.rollback()
        raise ConnectionException("A database connection error occurred while registering IoT devices.")

    finally:
        cursor.close()
        release_connection(connection)



# da bi dobili ID korisnikovih iot-a
def GetIoTDevicesByUserId(user_id: int) -> list[dict]:
    query = """
        SELECT * FROM iot_devices WHERE user_id = %s
    """
    connection = getConnection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        # Convert base_consumption_watts to float
        for device in result:
                device["base_consumption_watts"] = float(device["base_consumption_watts"])
                device["added_date"]=     device["added_date"].timestamp()


        return result
    except Exception as e:
        raise ConnectionException("Failed to fetch IoT devices.") from e
    finally:
        cursor.close()
        release_connection(connection)
