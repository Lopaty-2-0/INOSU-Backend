from flask import Flask
import sqlalchemy as sql

app = Flask(__name__)

#We love Markétka <3
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root@localhost/marketkaDB'
app.config['SECRET_KEY'] = ''

db = sql(app)