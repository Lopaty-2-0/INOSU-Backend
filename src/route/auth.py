from app import  db
from flask import jsonify, Blueprint
from utils.response import sendResponse
from models import User

routes_bp = Blueprint('routes', __name__)

@routes_bp.errorhandler(404)
def page_not_found(e):
    return jsonify(sendResponse(e, 1, {"message": "Page not found"}, "error")), 404

@routes_bp.errorhandler(500)
def server_error(e):
    return  jsonify(sendResponse(e, 2,  {"message": "Internal server error" }, "error")), 500

@routes_bp.route("/")
def index():
    return 

@routes_bp.route("/registration", methods=['POST'])
def registration(name, surname, abbreviation, role, password, profilePicture, email, idClass):
    if not name:
        return  jsonify(sendResponse(400, 3,  {"message": "Name is not entered" }, "error"))
    if not surname:
        return  jsonify(sendResponse(400, 4,  {"message": "Surname is not entered" }, "error"))
    if not role:
        return  jsonify(sendResponse(400, 5, {"message": "Role is not entered" }, "error"))
    if not password:
        return  jsonify(sendResponse(400, 6,  {"message": "Password is not entered" }, "error"))
    if len(str(password)) < 5:
        return  jsonify(sendResponse(400, 7,  {"message": "Password is too short" }, "error"))
    if not email:
        return  jsonify(sendResponse(400, 8,  {"message": "Email is not entered" }, "error"))
    

    newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = password, profilePicture = profilePicture, email = email, idClass = idClass)

    db.session.add(newUser)
    db.session.commit()

@routes_bp.route("/login", methods=['POST'])
def login(login, password):
    if not login or not password:
        return jsonify(sendResponse(400, 9,  {"message": "Email or password not entered" }, "error"))
    
