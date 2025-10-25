import flask_login
import os
from src.utils.response import send_response
from src.utils.ssh_connect import ssh_connect
from src.create_DB import create_db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql
from datetime import timedelta
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_cors import CORS
from flask_migrate import Migrate
from src.utils.enums import Role

load_dotenv(".env", override=False)
load_dotenv(".env.hmac", override=True)
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
psw = os.getenv("DB_PSW")
database = os.getenv("DB_NAME")
secret_key = os.getenv("SECRET_KEY")
task_path = os.getenv("TASK_PATH")
pfp_path = os.getenv("PFP_PATH")
url = os.getenv("URL")

try:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://" + user + ":" + psw + "@" + host + "/" + database

    app.config["SECRET_KEY"] = secret_key.encode("utf-8")
    app.config["JWT_SECRET_KEY"] = secret_key.encode("utf-8")
    app.config["UPLOAD_FOLDER"] = "/files/profilePictures"
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = True
    app.config["REMEMBER_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days = 30)
    app.config["REMEMBER_COOKIE_REFRESH_EACH_REQUEST"] = True
    app.config["MAX_CONTENT_LENGTH"] = 32*1024*1024
    
    ssh = ssh_connect()
    db = sql(app)
    jwt = JWTManager(app)
    migrattion = Migrate(app, db)
    CORS( 
        app,
        supports_credentials=True,
        origins=["http://localhost:3000", "http://100.114.228.127", "http://100.114.228.127:3000", "https://100.114.228.127"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = ""

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @jwt.expired_token_loader
    def expired_token(expiredToken, nn):
        return send_response(401, "JWT16010", {"message": "Token is expired"}, "error")
    
    @jwt.invalid_token_loader
    def invalid_token(e):
        return send_response(422, "JWT16020", {"message": e}, "error")

    with app.app_context():
        from src.models.User_Class import User_Class
        from src.models.User import User
        from src.models.Class import Class
        from src.models.Task import Task
        from src.models.Specialization import Specialization
        from src.models.User_Team import User_Team
        from src.models.Team import Team

        db.create_all()

        if not User.query.filter_by(role = Role.Admin).first():
            newUser = User(name = "admin", surname = "admin", abbreviation = None, role = Role.Admin, password = generate_password_hash("admin"), profilePicture = None, email = "admin@admin.cz")
            db.session.add(newUser)
            db.session.commit()
        
    from src.route.routes_bp import routes_bp
    app.register_blueprint(routes_bp)
except OperationalError as db_error:
    try:
        create_db(gHost=host, gUser=user, gPasswd=psw, gDatabase=database)
        print("Creating database")
        print("Please run program once more")
    except Exception as e:
        print(f"Error while creating database: {e}")
    finally:
        exit()
except Exception as e:
    print(f"Error while starting aplication: {e}")
    exit()
