from app import  db
from flask import Blueprint, request
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
    if User.query.filter_by(abbreviation = abbreviation).first():
        return  sendResponse(400, 11,  {"message": "Abbreviation is already in use" }, "error")
    if not idClass:
        idClass = None

    
    db.session.add(User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = password, profilePicture = profilePicture, email = email, idClass = idClass))
    db.session.commit()

    return sendResponse(1,8,{"message" : "User created succesfuly"}, "succes")

@routes_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json(force=True)
    login = str(data["login"])
    password = str(data["password"])

    if not login or not password:
        return sendResponse(400, 10,  {"message": "Email or password not entered" }, "error")
    
    #dont know if works, probably not, will test later
    if User.query.filter_by(email = login) or User.query.filter_by(abbreviation = login):
        if User.query.filter_by(password = password):
            return sendResponse(400, 12, {"message": "Login succesful", "User":"smrdí mi koule"}, "succes")

    return sendResponse(400,13,{"message": "Wrong email or password"}, "error")

@routes_bp.route("/logout")
def logout():
    return

@routes_bp.route("/verification")
def verification():
    return