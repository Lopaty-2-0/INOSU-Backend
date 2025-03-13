import mysql.connector
def create_db(gHost, gUser, gPasswd, gDatabase):
    create_db = mysql.connector.connect(
        host = str(gHost),
        user = str(gUser),
        passwd = str(gPasswd),
        auth_plugin = "mysql_native_password"
    )

    cursor = create_db.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{gDatabase}`")

    cursor.execute("SHOW DATABASES")

    for db in cursor:
        print(db)