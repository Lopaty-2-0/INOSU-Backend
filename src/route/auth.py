from app import  db
import flask_login
from sqlalchemy import or_
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from src.utils.response import sendResponse
from src.models.User import User
import datetime

routes_bp = Blueprint("routes", __name__)



@routes_bp.route("/")
def index():
    return sendResponse(200, 2, {"message": "This is index", "time": datetime.datetime.now}, "succes")

@routes_bp.route("/registration", methods = ["POST"])
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
    if abbreviation !=  "":
        if User.query.filter_by(abbreviation = abbreviation).first():
            return  sendResponse(400, 11,  {"message": "Abbreviation is already in use" }, "error")
    else:
        abbreviation = None
    if not idClass:
        idClass = None

    newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = generate_password_hash(password), profilePicture = profilePicture, email = email, idClass = idClass)
    db.session.add(newUser)
    db.session.commit()

    return sendResponse(201,8,{"message" : "User created succesfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role, "profilePicture": newUser.profilePicture, "email": newUser.email, "idClass": newUser.idClass}}, "succes")

@routes_bp.route("/login", methods = ["POST"])
def login():
    data = request.get_json(force = True)
    login = str(data["login"])
    password = str(data["password"])

    if not login or not password:
        return sendResponse(400, 10, {"message": "Email or password not entered" }, "error")

    user = User.query.filter(or_(User.email == login, User.abbreviation == login)).first()

    if not user or not check_password_hash(user.password, password):
        return sendResponse(401, 13, {"message": "Wrong login or password"}, "error")
    
    flask_login.login_user(user)
    return sendResponse(200, 12, {"message": "Login successful", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")

@routes_bp.route("/logout", methods = ["POST"])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return sendResponse(200, 12, {"message": "Logged out"}, "succes")

@routes_bp.route("/verification")
def verification():
    return