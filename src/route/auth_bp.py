import flask_login
from sqlalchemy import or_
from flask import Blueprint, request
from werkzeug.security import check_password_hash
from src.utils.response import sendResponse
from src.models.User import User
from src.utils.allUserClasses import allUserClasses

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/login", methods = ["POST"])
def login():
    data = request.get_json(force = True)
    login = data.get("login", None)
    password = str(data.get("password", None))
    stayLogged = bool(data.get("stayLogged", None))

    if not login or not password:
        return sendResponse(400, 6010, {"message": "Login or password not entered"}, "error")

    user = User.query.filter(or_(User.email == login, User.abbreviation == login.upper())).first()

    if not user or not check_password_hash(user.password, password):
        return sendResponse(400, 6020, {"message": "Wrong login or password"}, "error")
    
    flask_login.login_user(user, remember = stayLogged)

    return sendResponse(200, 6031, {"message": "Login successful", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": allUserClasses(user.id), "createdAt":user.createdAt}}, "success")

@auth_bp.route("/auth/logout", methods = ["DELETE"])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return sendResponse(200, 7011, {"message": "Logged out"}, "success")

@auth_bp.route("/auth/verify", methods=["GET"])
def verifyUser():
    if not flask_login.current_user.is_authenticated:
        state = False
        message = "User not logged in"
        role = None
        id = None
    else:
        state = True
        message = "User logged in"
        role = flask_login.current_user.role
        id = flask_login.current_user.id
    return sendResponse(200, 17011, {"message":message,"logged": state, "role":role, "id":id}, "success")