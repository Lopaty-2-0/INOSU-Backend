import mysql.connector
def create_db():
    create_db = mysql.connector.connect(
        host = "localhost",
        user = "root",
        passwd = ""
    )

    cursor = create_db.cursor()

    cursor.execute("CREATE DATABASE marketkaDB")

    cursor.execute("SHOW DATABASES")

    for db in cursor:
        print(db)