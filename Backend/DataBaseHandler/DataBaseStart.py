import mysql.connector
import json
import logging
from mysql.connector import pooling
from dotenv import load_dotenv
import os
import time
# MySQLConverter inherits from MySQLConverterBase, so using MySQLConverter is generally fine.
from mysql.connector.conversion import MySQLConverter, MySQLConverterBase


from ..CustomException import *

connection_pool = None

# --- The most robust CustomMySQLConverter Class for DECIMAL to float ---
class CustomMySQLConverter(MySQLConverter):
    def _to_python_decimal(self, value):
        """
        Converts a MySQL DECIMAL/NUMERIC value to a Python float.
        This method is specifically called by mysql-connector-python
        when it encounters a DECIMAL or NEWDECIMAL field.
        """
        if value is None:
            return None
        try:
            # The 'value' here is typically a string or a bytes object
            # representing the decimal number. Python's float() can parse this.
            return float(value)
        except (ValueError, TypeError) as e:
            # Log the error or handle it as appropriate for your application
            logging.error(f"Error converting DECIMAL to float: {value}. Error: {e}")
            return None # Or raise a specific error if conversion is critical


env_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    '..', # Go up from DataBaseHandler to Backend
    '..', # Go up from Backend to Praksa
    'devinfoDocker.env' # Then specify the .env file
))
load_dotenv(env_path)
DB_HOST = os.getenv('MYSQL_HOST')
DB_USER = os.getenv('MYSQL_USER')
DB_PORT = os.getenv('MYSQL_PORT') 
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_NAME = os.getenv('MYSQL_DB_NAME')

POOL_NAME = "mysql_connection_pool"
POOL_SIZE = 10 


def initializePool():
    global connection_pool
    try:
        if connection_pool is None:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name=POOL_NAME,
                pool_size=POOL_SIZE,
                host = DB_HOST,
                user = DB_USER,
                port = DB_PORT,
                password =DB_PASSWORD,
                database = DB_NAME,
                converter_class=CustomMySQLConverter

                )

    #mi cemo kod API-ja hvatati ovaj exception i returnovati  return jsonify({"error": "Internal server error. Please try again later."}), 500
    except Exception as e:
        logging.error(f"Error initializing connection pool: {e}", exc_info=True)
        raise Exception("Failed to initialize database connection pool") from e
    


def getConnection(max_tries =6, timeout=0.5):
    global connection_pool
    if connection_pool is None:
        initializePool()

    tries=0

    while tries<max_tries:
        try:
            #ovde pokusavamo da dobijemo konekciju iz pool-a
            return connection_pool.get_connection()                 #posto je globalna prom u inicijalizaciji se connection_pool = pooling.MySQLConnectionPool(...) uradi 
        except mysql.connector.Error as e:
            tries+=1
            logging.error(f"Attempt {tries}/{max_tries}: Connection pool exhausted. Error: {e}")
            time.sleep(timeout)

    logging.error(f"Failed to get a connection from the pool after {max_tries} retries.")
    raise Exception("Failed to get a connection from the pool after multiple retries.")



def release_connection(connection):
    try:
        if connection and  connection.is_connected():
            connection.close()
            logging.info("Connection released successfully.")
        else:
            logging.warning("Connection was already closed or invalid.")
    except mysql.connector.Error as e:
        logging.error(f"Error while releasing connection: {e}")


#initializePool()
