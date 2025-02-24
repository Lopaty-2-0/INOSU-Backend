from src.utils.response import sendResponse
from flask import request, Blueprint
import flask_login
from app import  db

user_bp = Blueprint("user", __name__)

@user_bp.route("/update", methods = ["POST"])
@flask_login.login_required

def update():
    data = request.get_json(force = True)
    name = str(data["name"])
    surname = str(data["surname"])
    abbreviation = str(data["abbreviation"])
    role = str(data["role"])
    profilePicture = data["profilePicture"]
    email = str(data["email"])
    password = str(data["password"])
    idClass = str(data["idClass"])

    if not name and not surname and not abbreviation and not role and not profilePicture and not email and not password and not idClass:
        return sendResponse(400, 10, {"message": "Nothing entered to change"}, "error")
    
    change = {"name": name, "surname": surname, "abbreviation": abbreviation, "role": role, "profilePicture": profilePicture, "email": email, "idClass": idClass}

    user = flask_login.current_user

    #will change, probably
    if not name:
        name = user.name
    if not surname:
        surname = user.surname
    if not abbreviation:
        abbreviation = user.abbreviation
    if not role:
        role = user.role
    if not profilePicture:
        profilePicture = user.profilePicture
    if not email:
        email = user.email
    if not password:
        password = user.password
    if not idClass:
        idClass = user.idClass

    user.name = name  
    user.surname = surname
    user.abbreviation = abbreviation
    user.role = role
    user.profilePicture = profilePicture
    user.email = email
    user.password = password
    user.idClass = idClass

    db.session.commit()

    return sendResponse(200, 12, {"message": "User changed succesfuly", "changed": change, "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "succes")