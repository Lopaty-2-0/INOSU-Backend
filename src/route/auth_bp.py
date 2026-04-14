
import flask_login
from sqlalchemy import or_
from flask import Blueprint, request, session, make_response
from werkzeug.security import check_password_hash
from src.utils.response import send_response
from src.models.User import User
from src.utils.all_user_classes import all_user_classes
from app import limiter

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/auth/login", methods = ["POST"])
@limiter.limit("5/minute")
def login():
    data = request.get_json(force = True)
    login = data.get("login", None)
    password = str(data.get("password", None))
    stayLogged = bool(data.get("stayLogged", None))

    if not login or not password:
        return send_response(400, 6010, {"message": "Login or password not entered"}, "error")

    user = User.query.filter(or_(User.email == login, User.abbreviation == login.upper())).first()

    if not user or not check_password_hash(user.password, password):
        return send_response(400, 6020, {"message": "Wrong login or password"}, "error")
    
    flask_login.login_user(user, remember = stayLogged)

    return send_response(200, 6031, {"message": "Login successful", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}}, "success")

@auth_bp.route("/auth/logout", methods = ["DELETE"])
@flask_login.login_required
@limiter.limit("30/minute")
def logout():
    flask_login.logout_user()
    session.clear()
    
    resp = make_response({"statuscode": 200, "resCode": 7011, "data": {"message": "Logged out"}, "resType": "success"}, 200) # zde je nutné přímo použít jejich make_response, jinak nelze smazat tu cookie
    resp.delete_cookie("remember_token")
    
    return resp

@auth_bp.route("/auth/verify", methods=["GET"])
@limiter.limit("120/minute")
def verify():
    if not flask_login.current_user.is_authenticated:
        state = False
        message = "User not logged in"
        role = None
        id = None
        updatedAt = None
    else:
        state = True
        message = "User logged in"
        role = flask_login.current_user.role.value
        id = flask_login.current_user.id
        updatedAt = flask_login.current_user.updatedAt
    return send_response(200, 17011, {"message":message,"logged": state, "role":role, "id":id, "updatedAt": updatedAt}, "success")