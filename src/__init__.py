from flask import Flask
import sqlalchemy as sql

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/test'
app.config['SECRET_KEY'] = ''

db = sql(app)