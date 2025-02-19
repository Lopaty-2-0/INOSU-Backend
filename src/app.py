from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql




app = Flask(__name__)



#We love Markétka <3

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/marketkaDB'
app.config['SECRET_KEY'] = ''


db = sql(app)


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