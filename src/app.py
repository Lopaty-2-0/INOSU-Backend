from flask import Flask
from flask_sqlalchemy import SQLAlchemy as sql
from createDB import creatussy




app = Flask(__name__)



#We love Markétka <3
#We need Markétka in our life
#We want Markétka in our life


creatussy()
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