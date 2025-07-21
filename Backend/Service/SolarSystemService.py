from ..DataBaseHandler import *                #importujemo DataBase Handlere, tu se nalazi RegisterUser



def RegisterSolarSystemService(solar_system: dict, user_id: int, battery_id: int = None) -> dict:
    """
    Servis za registraciju solarnog sistema.
    Validira podatke, i prosleđuje ih ka bazi podataka.
    
    Vraća ID novounetog solarnog sistema, kako bi se mogao povezati sa baterijom.

    Raises:
        IlegalValuesException: Ako su vrednosti nevalidne.
    """


    # system_name: ne sme biti prazan i maksimalno 255 karaktera
    system_name = solar_system.get("system_name")
    if not system_name or not isinstance(system_name, str) or len(system_name) > 255:
        raise IlegalValuesException("System name must be a non-empty string of max 255 characters.")

    # system_type: mora biti jedan od dozvoljenih
    system_type = solar_system.get("system_type")
    if system_type not in ["grid_tied", "grid_tied_hybrid"]:
        raise IlegalValuesException("System type must be either 'grid_tied' or 'grid_tied_hybrid'.")

    # total_panel_wattage_wp: broj > 0
    total_panel_wattage_wp = solar_system.get("total_panel_wattage_wp")
    if not isinstance(total_panel_wattage_wp, (int, float)) or total_panel_wattage_wp <= 0:
        raise IlegalValuesException("Total panel wattage must be a positive number.")

    # inverter_capacity_kw: broj > 0
    inverter_capacity_kw = solar_system.get("inverter_capacity_kw")
    if not isinstance(inverter_capacity_kw, (int, float)) or inverter_capacity_kw <= 0:
        raise IlegalValuesException("Inverter capacity must be a positive number.")

    base_consumption_kwh = solar_system.get("base_consumption_kwh")

    if not isinstance(base_consumption_kwh, (int, float)) or base_consumption_kwh <= 0:
        raise IlegalValuesException("base consumption kwh  must be a positive number.")

    # battery_id: ako je sistem 'grid_tied' onda baterija ne sme biti prosledjena
    if system_type == "grid_tied" and battery_id is not None:
        raise IlegalValuesException("Grid-tied systems should not have a battery assigned.")
    
    # Ako je sistem 'grid_tied_hybrid' baterija mora biti prosledjena
    if system_type == "grid_tied_hybrid" and battery_id is None:
        raise IlegalValuesException("Hybrid systems must have a battery assigned.")

    
    solar_data_for_db = {
        "system_name": system_name,
        "system_type": system_type,
        "total_panel_wattage_wp": total_panel_wattage_wp,
        "inverter_capacity_kw": inverter_capacity_kw,
        "base_consumption_kwh":base_consumption_kwh
    }

    return RegisterSolarSystem(solar_data_for_db, user_id, battery_id)


def GetSolarSystemByUserIdService(user_id:int)->dict:

    return GetSolarSystemByUserId(user_id)