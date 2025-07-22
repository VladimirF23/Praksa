from ..DataBaseHandler import *




def RegisterIoTService(devices: list[dict], user_id: int, system_id: int)->bool:
    """
    Validira listu IoT uredjaja (dictionaries) i delegira insertion ka DBHandleru

    :param devices: Lista dictionari-a sa device info
    :param user_id: ID korisnika koji poseduje ove IoT
    :param solar_system_id: ID solarnog sistema kom IoT pripada
    """
    if not devices or not isinstance(devices, list):
        raise IlegalValuesException("You must provide a list of at least one IoT device.")

    validated_devices = []
    all_errors = []

    for idx, device in enumerate(devices, start=1):
        device_name            = device.get("device_name")
        device_type            = device.get("device_type")
        base_consumption_watts = device.get("base_consumption_watts")
        priority_level         = device.get("priority_level", "medium")
        current_status         = device.get("current_status", "off")
        is_smart_device        = device.get("is_smart_device", False)
        
        errors = []

        if not device_name:
            errors.append(f"[Device {idx}] Name can't be NULL.")
        if not isinstance(base_consumption_watts, (int, float)) or base_consumption_watts <= 0:
            errors.append(f"[Device {idx}] Base consumption must be a positive number.")
        if priority_level not in ['critical', 'medium', 'low', 'non_essential']:
            errors.append(f"[Device {idx}] Invalid priority level.")
        if current_status not in ['on', 'off']:
            errors.append(f"[Device {idx}] Invalid current status.")
        if not isinstance(is_smart_device, bool):
            errors.append(f"[Device {idx}] Smart device flag must be boolean.")

        if errors:
            all_errors.extend(errors)
        else:
            validated_devices.append({
                "device_name": device_name,
                "device_type": device_type,
                "base_consumption_watts": base_consumption_watts,
                "priority_level": priority_level,
                "current_status": current_status,
                "is_smart_device": is_smart_device,
            })

    if all_errors:
        raise IlegalValuesException(" ".join(all_errors))
    

    return RegisterIoTDevices(validated_devices, user_id, system_id)
    

#vratimo sve IoT koji pripadju user-u bitan nam je njhiv id
def GetUsersIOTsService(user_id:int) ->list[dict]:

    return GetIoTDevicesByUserId(user_id)



