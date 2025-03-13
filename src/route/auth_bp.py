import flask_login
from sqlalchemy import or_
from flask import Blueprint, request
from werkzeug.security import check_password_hash
from src.utils.response import sendResponse
from src.models.User import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/login", methods = ["POST"])
def login():
    data = request.get_json(force = True)
    login = str(data["login"])
    password = str(data["password"])
    stayLogged = data["stayLogged"]

    stayLogged = bool(stayLogged)

    if not login or not password:
        return sendResponse(400, 6010, {"message": "Email or password not entered"}, "error")

    user = User.query.filter(or_(User.email == login, User.abbreviation == login.upper())).first()

    if not user or not check_password_hash(user.password, password):
        return sendResponse(400, 6020, {"message": "Wrong login or password"}, "error")
    
    flask_login.login_user(user, remember = stayLogged)

    return sendResponse(200, 6031, {"message": "Login successful", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")

@auth_bp.route("/auth/logout", methods = ["DELETE"])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return sendResponse(200, 7011, {"message": "Logged out"}, "success")
