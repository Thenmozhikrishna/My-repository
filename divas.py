import mysql.connector
from mysql.connector import Error

print("Script is starting...")  # Confirm the script starts

try:
    print("Attempting to connect to MySQL...")  # Before connection
    mydb = mysql.connector.connect(
        host="10.10.201.236",
        user="adwaita_demo",
        password="f6Q28fE765vLsN"
    )
    print("Connection object created.")  # After connection attempt

    if mydb.is_connected():
        print("Connection to MySQL successful!")
    else:
        print("Failed to connect to MySQL.")

except Error as e:
    print(f"An error occurred: {e}")  # Catch and display any error

finally:
    print("Checking if connection needs to close...")
    if 'mydb' in locals() and mydb.is_connected():
        mydb.close()
        print("MySQL connection is closed.")
    else:
        print("Connection was never established or already closed.")

print("Script execution complete.")
