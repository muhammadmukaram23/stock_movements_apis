import mysql.connector
from fastapi import HTTPException

def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="inventory_management_system",
              # Use dictionary cursor for named access to columns
        )
        return conn
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database connection error: {err}") 