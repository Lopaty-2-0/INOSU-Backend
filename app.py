import flask_login
import os
from src.createDB import creatussy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql
from datetime import timedelta

try:

    app = Flask(__name__)

    #We love Markétka <3
    #We need Markétka in our life
    #We want Markétka in our life


    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@localhost/marketkaDB"

    #must change later
    app.config["SECRET_KEY"] = "Markétka je naše bohyně".encode("utf-8")
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days = 30)

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
        creatussy()
    except:
        print("Database is not running")
        os._exit(1)
