from ..DataBaseHandler import *                #importujemo DataBase Handlere, tu se nalazi RegisterBattery



#RADI BOLJEG TESTIRANJA BATERIJE NEMOJ DODATI DODATNA OGRANICENJA NA OSTALE PARAMATRE !!!!

def RegisterBatteryService(battery: dict) -> dict:
    """
    Returns:
        int: ID novo kreirane baterije da bi se taj id mogao prosledi solarnom systemu

    Raises:
        IlegalValuesException: Ako neki obavezni parametar nije validan.
    """


    # Proveravamo da li postoje svi obavezni parametri
    if battery["capacity_kwh"] is None:
        raise IlegalValuesException(f"Batteries capacity_kwh is missing")

    # Validacija: capacity_kwh mora biti pozitivan broj
    if not isinstance(battery["capacity_kwh"], (int, float)) or battery["capacity_kwh"] <= 0:
        raise IlegalValuesException("Battery capacity must be a positive number.")

    # default vrednost current_charge_percentage ako nije uneta
    if "current_charge_percentage" not in battery or battery["current_charge_percentage"] is None:
        battery["current_charge_percentage"] = 100.0  # Pretpostavljamo da je nova baterija puna

    return RegisterBattery(battery)




def AddSolarSystemToBatteryService(battery_id,system_id) -> bool:
    """
    Posle pravljanja solarnog sistema potrebno je prosledi id njega ka id vec postojece baterije
    Args:
        battery_id (int): ID baterije.
        solar_system_id (int): ID solarnog sistema.

    Returns:
        bool: True ako je povezivanje uspešno.

    Raises:
        IlegalValuesException: Ako su ID-evi nevalidni ili već povezani.
        ConnectionException: Ako dodje do problema sa konekcijom.
    """

    # Validacija: ID-evi moraju biti pozitivni brojevi
    if not isinstance(battery_id, int) or battery_id <= 0:
        raise IlegalValuesException("Battery ID must be a positive integer.")
    if not isinstance(system_id, int) or system_id <= 0:
        raise IlegalValuesException("Solar System ID must be a positive integer.")

    return AddSolarSystemToBattery(battery_id, system_id)

def GetBatteryDataService(battery_id:int)->dict:

    return  GetBatteryData(battery_id)


def UpdateBatteryCurrentPercentageService(battery_id:int,new_percentage: float)->bool:

    return update_battery_percentage(battery_id,new_percentage)






def DeleteBatteryForUserService(battery_id: int) -> bool:


    # 3. Pozvati DB funkciju za brisanje
    success = DeleteBattery(battery_id) # <--- Koristi novu DB funkciju
    
    return success