import flask_login
from src.utils.response import sendResponse
from sqlalchemy import delete
from werkzeug.security import generate_password_hash
from flask import request, Blueprint
from app import  db
from src.models.User import User
import re

user_bp = Blueprint("user", __name__)

email_regex = r"^\S+@\S+\.\S+$"

@user_bp.route("/user/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role == "admin":
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
            return sendResponse(400, 3, {"message": "Name is not entered"}, "error")
        if  not surname:
            return sendResponse(400, 4, {"message": "Surname is not entered"}, "error")
        if not role:
            return sendResponse(400, 5,{"message": "Role is not entered"}, "error")
        if not password:
            return sendResponse(400, 6, {"message": "Password is not entered"}, "error")
        if len(str(password)) < 5:
            return  sendResponse(400, 7, {"message": "Password is too short"}, "error")
        if not email:
            return sendResponse(400, 8, {"message": "Email is not entered"}, "error")
        if not re.match(email_regex, email):
            return sendResponse(400, 9, {"message": "Wrong email format"}, "error")
        if User.query.filter_by(email = email).first():
            return sendResponse(400, 9, {"message": "Email is already in use"}, "error")
        if abbreviation:
            if User.query.filter_by(abbreviation = abbreviation).first():
                return sendResponse(400, 11, {"message": "Abbreviation is already in use"}, "error")
        else:
            abbreviation = None
        if not idClass:
            idClass = None

        newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = generate_password_hash(password), profilePicture = profilePicture, email = email, idClass = idClass)
        db.session.add(newUser)
        db.session.commit()

        return sendResponse(201,8,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role, "profilePicture": newUser.profilePicture, "email": newUser.email, "idClass": newUser.idClass}}, "success")
    return sendResponse(400, 11, {"message": "No permission for that"}, "error")

@user_bp.route("/user/update", methods = ["POST"])
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
    idUser = str(data["idUser"])
    
    user = flask_login.current_user

    #will change, probably
    if not idUser:

        if not profilePicture and not password:
            return sendResponse(400, 10, {"message": "Nothing entered to change"}, "error")
        if profilePicture:
            user.profilePicture = profilePicture
        if password:
            if len(str(password)) < 5:
                return  sendResponse(400, 7, {"message": "Password is too short"}, "error")
            password = generate_password_hash(password)
            user.password = password

        db.session.commit()
        return sendResponse(200, 12, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")
    else:
        if str(user.role).lower() == "admin":
            if not name and not surname and not abbreviation and not role and not profilePicture and not email and not password and not idClass:
                return sendResponse(400, 10, {"message": "Nothing entered to change"}, "error")

            secondUser = User.query.filter_by(id = idUser).first()
            if secondUser:
                if name:
                    secondUser.name = name  
                if surname:
                    secondUser.surname = surname
                if abbreviation:
                    secondUser.abbreviation = abbreviation
                if role:
                    secondUser.role = role
                if profilePicture:
                    secondUser.profilePicture = profilePicture
                if email:
                    if not re.match(email_regex, email):
                        return sendResponse(400, 9, {"message": "Wrong email format"}, "error")
                    secondUser.email = email
                if password:
                    if len(str(password)) < 5:
                        return sendResponse(400, 7, {"message": "Password is too short"}, "error")
                    password = generate_password_hash(password)
                    secondUser.password = password
                if idClass:
                    secondUser.idClass = idClass            

                db.session.commit()

                return sendResponse(200, 12, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role, "profilePicture": secondUser.profilePicture, "email": secondUser.email, "idClass": secondUser.idClass}}, "success")
            return sendResponse(400, 11, {"message": "Wrong user id"}, "error")
        return sendResponse(400, 11, {"message": "No permission for that"}, "error")
        
@user_bp.route("/user/delete", methods = ["POST"])
@flask_login.login_required

def delete():
    data = request.get_json(force = True)
    idUser = data["idUser"]
    goodIds = []
    badIds = []

    if flask_login.current_user.role == "admin":
        if not idUser:
            return sendResponse(400, 11, {"message": "No idUser"}, "error")
        try:
            id = int(idUser)
            try:
                delUser = User.query.filter_by(id = id).first()
                db.session.delete(delUser)
                goodIds.append(id)
            except:
                badIds.append(id)
            db.session.commit()
            print("penis")
        except:
            for id in idUser:
                try:
                    delUser = User.query.filter_by(id = id).first()
                    db.session.delete(delUser)
                    goodIds.append(id)
                except:
                    badIds.append(id)
                db.session.commit()
        return sendResponse(200, 12, {"deletedIds": goodIds, "notdeletedIds": badIds}, "success")
    return sendResponse(400, 11, {"message": "No permission for that"}, "error")