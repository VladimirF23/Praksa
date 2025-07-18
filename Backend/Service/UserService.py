from ..DataBaseHandler import *                #importujemo DataBase Handlere, tu se nalazi RegisterUser
import bcrypt
import re


#za heshiranje sifre
def HashPassword(password:str)->str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'),salt)      #encoduje se u byte
    return hashed_password.decode('utf-8')  #da ga vratimo iz byte-a u string da bi mogao u bazi da bude storovan



def RegisterUserService(user:dict):
    """
    Registracioni service koji prosledjuje DBHandleru parametre korisnika za registraciju
    Hash-uje sifru korisnika
    """

    if len(user["password"]) > 256 or len(user["password"]) < 8:
        raise IlegalValuesException("Password does not meet the minimum/maximum length requirement.")

    # Exception za username duzinu
    if len(user["username"]) > 50:
        raise IlegalValuesException("Username does not meet the maximum length requirement.")

    # Exception za email duzinu
    if len(user["email"]) > 100:
        raise IlegalValuesException("Email does not meet the maximum length requirement.")

    # Email regex validation
    if re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", user["email"]) is None:
        raise IlegalValuesException("Email does not meet the requirement.")

    # Validacija house_size_sqm
    if not isinstance(user.get("house_size_sqm"), (int, float)) or user["house_size_sqm"] <= 0:
        raise IlegalValuesException("Invalid value for house_size_sqm. It must be a positive number.")

    # Validacija num_household_members
    if not isinstance(user.get("num_household_members"), int) or user["num_household_members"] <= 0:
        raise IlegalValuesException("Invalid value for num_household_members. It must be a positive integer.")

    # Validacija latitude and longitude
    if not isinstance(user.get("latitude"), (int, float)) or not (-90 <= user["latitude"] <= 90):
        raise IlegalValuesException("Invalid value for latitude. It must be between -90 and 90.")
    if not isinstance(user.get("longitude"), (int, float)) or not (-180 <= user["longitude"] <= 180):
        raise IlegalValuesException("Invalid value for longitude. It must be between -180 and 180.")




    password_hash = HashPassword(user["password"])

    # Prepare the dictionary with all required fields for RegisterUser
    user_data_for_db = {
        "username": user["username"],
        "email": user["email"],
        "password_hash": password_hash,
        "house_size_sqm": user["house_size_sqm"],
        "num_household_members": user["num_household_members"],
        "latitude": user["latitude"],
        "longitude": user["longitude"]
    }

    if "user_type" in user:
        user_data_for_db["user_type"] = user["user_type"]

    RegisterUser(user_data_for_db)                  #poziv DataBase Layer-a, tu se nalaze exceptionu za unos vec postojeceg email-a ili username-a