import flask_login
import os
from src.utils.response import sendResponse
from src.createDB import create_db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql
from datetime import timedelta
from werkzeug.security import generate_password_hash
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
psw = os.getenv("DB_PSW")
database = os.getenv("DB_NAME")
secret_key = os.getenv("SECRET_KEY")

try:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://" + user + ":" + psw + "@" + host + "/" + database

    app.config["SECRET_KEY"] = secret_key.encode("utf-8")
    app.config["JWT_SECRET_KEY"] = secret_key.encode("utf-8")
    app.config["UPLOAD_FOLDER"] = "/files/profilePictures"
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days = 30)
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = False # HTTPS is not used
    app.config["REMEMBER_COOKIE_SAMESITE"] = None
    app.config["SESSION_COOKIE_SAMESITE"] = None
    app.config["MAX_CONTENT_LENGTH"] = 32*1024*1024

    db = sql(app)
    jwt = JWTManager(app)
    cors = CORS(
        app,
        supports_credentials=True,
        origins=["http://localhost:3000"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With" "Content-Length", "Set-Cookie"],
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
        return sendResponse(401, "JWT16010", {"message": "Token is expired"}, "error")
    
    @jwt.invalid_token_loader
    def invalid_token(e):
        return sendResponse(422, "JWT16020", {"message": e}, "error")

    with app.app_context():
        from src.models.User import User
        from src.models.Class import Class
        from src.models.Task import Task
        from src.models.Specialization import Specialization
        from src.models.Team import Team
        from src.models.Task_Class import Task_Class

        db.create_all()

        if not User.query.filter_by(role = "admin").first():
            newUser = User(name = "admin", surname = "admin", abbreviation = "", role = "admin", password = generate_password_hash("admin"), profilePicture = None, email = "admin@admin.cz", idClass = None)
            db.session.add(newUser)
            db.session.commit()
        
    from src.route.routes_bp import routes_bp
    app.register_blueprint(routes_bp)
except:
    try:
        create_db(gHost=host, gUser=user, gPasswd=psw, gDatabase=database)
        print("Creating database")
        print("Please run program once more")
    except Exception as e:
        print(f"Error while creating database: {e}")
    exit() 
