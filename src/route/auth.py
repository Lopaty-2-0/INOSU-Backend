from app import  db, login_manager
import flask_login
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from utils.response import sendResponse
from models.User import User
import datetime

routes_bp = Blueprint('routes', __name__)

@routes_bp.errorhandler(404)
def page_not_found(e):
    return sendResponse(404, 1, {"message": "Page not found"}, "error")

@routes_bp.errorhandler(500)
def server_error(e):
    return  sendResponse(500, 2,  {"message": "Internal server error" }, "error")

@routes_bp.errorhandler(405)
def server_error(e):
    return  sendResponse(405, 3,  {"message": "Method Not Allowed" }, "error")

@routes_bp.route("/")
def index():
    return {"message": "My balls itch", "time": datetime.datetime.now}

@routes_bp.route("/registration", methods=['POST'])
def registration():
    data = request.get_json()
    name = str(data["name"])
    surname = str(data["surname"])
    abbreviation = str(data["abbreviation"])
    role = str(data["role"])
    profilePicture = data["profilePicture"]
    email = str(data["email"])
    password = str(data["password"])
    idClass = str(data["idClass"])

    if not name:
        return  sendResponse(400, 3,  {"message": "Name is not entered" }, "error")
    if not surname:
        return  sendResponse(400, 4,  {"message": "Surname is not entered" }, "error")
    if not role:
        return  sendResponse(400, 5, {"message": "Role is not entered" }, "error")
    if not password:
        return  sendResponse(400, 6,  {"message": "Password is not entered" }, "error")
    if len(str(password)) < 5:
        return  sendResponse(400, 7,  {"message": "Password is too short" }, "error")
    if not email:
        return  sendResponse(400, 8,  {"message": "Email is not entered" }, "error")
    if User.query.filter_by(email = email).first():
        return  sendResponse(400, 9,  {"message": "Email is already in use" }, "error")
    if abbreviation != "":
        if User.query.filter_by(abbreviation = abbreviation).first():
            return  sendResponse(400, 11,  {"message": "Abbreviation is already in use" }, "error")
    else:
        abbreviation = None
    if not idClass:
        idClass = None

    newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = generate_password_hash(password), profilePicture = profilePicture, email = email, idClass = idClass)
    db.session.add(newUser)
    db.session.commit()

    return sendResponse(1,8,{"message" : "User created succesfuly", "user": newUser.password}, "succes")

@routes_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json(force=True)
    login = str(data["login"])
    password = str(data["password"])

    user = User.query.filter_by(email = login).first()
    user2 = User.query.filter_by(abbreviation = login).first()

    if user:
        if check_password_hash(user.password, password):
            return sendResponse(400, 12, {"message": "Login succesful", "User":"smrdí mi koule"}, "succes")
    if user2:
        if check_password_hash(user2.password, password):
            return sendResponse(400, 12, {"message": "Login succesful", "User":"smrdí mi koule"}, "succes")
    return sendResponse(400,13,{"message": "Wrong login or password"}, "error")

@routes_bp.route("/logout", methods=['POST'])
@flask_login.login_required
def logout():
     flask_login.logout_user()
     return sendResponse(400, 12, {"message": "Logged out"}, "succes")

@routes_bp.route("/verification")
def verification():
    return