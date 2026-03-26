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
from src.utils.enums import Role, Type
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import redis
from flask_limiter import Limiter
from src.utils.limiter import get_user_id

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
hmac_ip = os.getenv("HMAC_IP")
redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = os.getenv("REDIS_PORT", 6379)
max_INT = 4294967295
max_FLOAT = 3.40e+38
max_TEXT = 65535

try:
    redis_port = int(redis_port)
except:
    redis_port = 6379

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
    app.config["MAX_CONTENT_LENGTH"] = 5*1024*1024*1024

    ssh = ssh_connect()
    app.ssh = ssh
    db = sql(app)
    jwt = JWTManager(app)
    migration = Migrate(app, db)
    scheduler = BackgroundScheduler()
    scheduler.start()
    redis_client = redis.Redis(host = redis_host, port = redis_port, db = 0, decode_responses = True)
    limiter = Limiter(key_func = get_user_id, app = app, default_limits=["60/minute"], storage_uri=f"redis://{redis_host}:{redis_port}")

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
    def load_user(userId):
        return User.query.get(int(userId))
    
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
        from src.models.Version_Team import Version_Team
        from src.models.Topic import Topic
        from src.models.Maturita import Maturita
        from src.models.Maturita_Task import Maturita_Task
        from src.models.Evaluator import Evaluator
        from src.models.Conversation import Conversation
        from src.models.Message import Message
        from src.models.Event import Event

        db.create_all()

        if not User.query.filter_by(role = Role.Admin).first():
            newUser = User(name = "admin", surname = "admin", abbreviation = None, role = Role.Admin, password = generate_password_hash("admin"), profilePicture = None, email = "admin@admin.cz")
            db.session.add(newUser)
            db.session.commit()
        
        from src.utils.reminder import create_reminder
        from src.utils.archive_conversation import create_archive_conversation

        now = datetime.datetime.now(datetime.timezone.utc)

        tasks = Task.query.filter(now <= Task.endDate)

        for task in tasks:
            user_teams = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor)

            for user_team in user_teams:
                student = User.query.filter_by(id = user_team.idUser).first()

                if student and student.reminders:
                    create_reminder(student.id, task.id, task.guarantor)

            if task.type == Type.Maturita:
                conversations = Conversation.query.filter_by(idTask = task.id, guarantor = task.guarantor)
                
                for conversation in conversations:
                    if conversation.idUser1 == task.guarantor:
                        user = User.query.filter_by(id = conversation.idUser2).first()
                    else:
                        user = User.query.filter_by(id = conversation.idUser1).first()
                    if user.role != Role.Student:
                        continue
                    
                    create_archive_conversation(conversation.idConversation, task.id, task.guarantor, conversation.idUser1, conversation.idUser2)
    
    from src.route.routes_bp import routes_bp
    app.register_blueprint(routes_bp)

    try:
        redis_client.ping()
    except redis.exceptions.ConnectionError as e:
        print("Problem with redis:", e)
        
except OperationalError as dbError:
    if dbError.orig.args[0] == 1049:
        try:
            create_db(gHost=host, gUser=user, gPasswd=psw, gDatabase=database)
            print("Creating database")
            print("Please run program once more")
        except Exception as e:
            print(f"Error while creating database: {e}")
        finally:
            exit()
    else:
        with app.app_context():
            db.create_all()
except Exception as e:
    print(f"Error while starting aplication: {e}")
    exit()