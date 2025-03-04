import flask_login
import os
from src.createDB import create_db
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql
from datetime import timedelta

load_dotenv()
host = os.getenv("HOST")
user = os.getenv("USER")
psw = os.getenv("PSW")
database = os.getenv("DATABASE")
secret_key = os.getenv("SECRET_KEY")

try:
    app = Flask(__name__)

    #We love Markétka <3
    #We need Markétka in our life
    #We want Markétka in our life

    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://" + user + ":" + psw + "@" + host + "/" + database

    #must change later
    app.config["SECRET_KEY"] = secret_key.encode("utf-8")
    app.config["UPLOAD_FOLDER"] = "/files/profilePictures"
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days = 30)
    app.config["MAX_CONTENT_LENGTH"] = 32*1024*1024

    db = sql(app)

    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = ""
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        from src.models.User import User
        from src.models.Class import Class
        from src.models.Task import Task
        from src.models.Specialization import Specialization
        from src.models.Team import Team
        from src.models.Task_Class import Task_Class

        db.create_all()
        
    from src.route.auth import auth_bp
    from src.route.errorhandlers import errors_bp
    from src.route.user import user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(user_bp)
except:
    try:
        create_db(gHost=host, gUser=user, gPasswd=psw, gDatabase=database)
        print("Creating database")
        print("Please run program once more")
    except Exception as e:
        print(f"Error while creating database: {e}")
    exit() 
