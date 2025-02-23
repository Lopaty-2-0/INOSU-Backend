from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql
import flask_login

app = Flask(__name__)

#We love Markétka <3
#We need Markétka in our life
#We want Markétka in our life

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root@localhost/marketkaDB"
#must change later
app.config["SECRET_KEY"] = "Markétka je naše bohyně"

db = sql(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = ""

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    from models.User import User
    from models.Class import Class
    from models.Task import Task
    from models.Specialization import Specialization
    from models.Team import Team
    from models.Task_Class import Task_Class

    db.create_all()
    
from route.auth import routes_bp
app.register_blueprint(routes_bp)