import datetime
import flask_login
from sqlalchemy import or_
from flask import Blueprint, request
from werkzeug.security import check_password_hash
from src.utils.response import sendResponse
from src.models.User import User
from src.utils.encodeFile import encode_file

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth", methods = ["GET"])
def index():
    return sendResponse(200, 6011, {"message": "This is auth index route", "time": datetime.datetime.now}, "success")

@auth_bp.route("/auth/login", methods = ["POST"])
def login():
    data = request.get_json(force = True)
    login = str(data["login"])
    password = str(data["password"])
    stayLogged = data["stayLogged"]

    stayLogged = bool(stayLogged)

    if not login or not password:
        return sendResponse(400, 7010, {"message": "Email or password not entered 1"}, "error")

    user = User.query.filter(or_(User.email == login, User.abbreviation == login.upper())).first()

    if not user or not check_password_hash(user.password, password):
        return sendResponse(401, 7020, {"message": "Wrong login or password"}, "error")
    
    pictures_path = "files/profilePictures/" + user.profilePicture
    encoded_file = encode_file(pictures_path)
    flask_login.login_user(user, remember = stayLogged)

    return sendResponse(200, 7031, {"message": "Login successful", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": encoded_file, "email": user.email, "idClass": user.idClass}}, "success")

@auth_bp.route("/auth/logout", methods = ["DELETE"])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return sendResponse(200, 8011, {"message": "Logged out"}, "success")
