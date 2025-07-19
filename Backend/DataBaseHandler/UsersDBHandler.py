from .DataBaseStart import *
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



