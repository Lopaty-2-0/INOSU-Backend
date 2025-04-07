import flask_login
import re
import json
import flask_jwt_extended
import datetime
from src.email.templates.resetPassword import emailResetPasswordTemplate
from src.utils.pfp import pfp
from src.models.Class import Class
from src.utils.response import sendResponse
from src.utils.sendEmail import sendEmail
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, Blueprint
from app import db
from src.models.User import User
from src.utils.checkFileSize import checkFileSize
from sqlalchemy import or_

user_bp = Blueprint("user", __name__)

email_regex = r"^\S+@\S+\.\S+$"
pfp_path = "files/profilePictures/"
pfp_extensions = {"jpg", "png", "jpeg"}
addUser_extensions = {"json"}

@user_bp.route("/user/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != "admin":
        return sendResponse(400, 1010, {"message": "No permission for that"}, "error")
    
    try:
        data = request.get_json()
        name = data.get("name", None)
        surname = data.get("surname", None)
        abbreviation = data.get("abbreviation", None)
        role = data.get("role", None)
        email = data.get("email", None)
        password = data.get("password", None)
        idClass = data.get("idClass", None)

        if not name:
            return sendResponse(400, 1020, {"message": "Name is not entered"}, "error")
        if len(name) > 100:
            return sendResponse(400, 1030, {"message": "Name too long"}, "error")
        if not surname:
            return sendResponse(400, 1040, {"message": "Surname is not entered"}, "error")
        if len(surname) > 100:
            return sendResponse(400, 1050, {"message": "Surname too long"}, "error")
        if not role:
            return sendResponse(400, 1060,{"message": "Role is not entered"}, "error")
        if len(role) > 45:
            return sendResponse(400, 1070, {"message": "Role too long"}, "error")
        if not password:
            return sendResponse(400, 1080, {"message": "Password is not entered"}, "error")
        if len(password) < 5:
            return  sendResponse(400, 1090, {"message": "Password is too short"}, "error")
        if not email:
            return sendResponse(400, 1100, {"message": "Email is not entered"}, "error")
        if not re.match(email_regex, email):
            return sendResponse(400, 1110, {"message": "Wrong email format"}, "error")
        if len(email) > 255:
            return sendResponse(400, 1120, {"message": "Email too long"}, "error")
        if User.query.filter_by(email = email).first():
            return sendResponse(400, 1130, {"message": "Email is already in use"}, "error")
        if abbreviation:
            if User.query.filter_by(abbreviation = abbreviation.upper()).first():
                return sendResponse(400, 1140, {"message": "Abbreviation is already in use"}, "error")
            if len(abbreviation) > 4:
                return sendResponse(400, 1150, {"message": "Abbreviation is too long"}, "error")
            abbreviation = abbreviation.upper()
        else:
            abbreviation = None
        if idClass:
            if not Class.query.filter_by(id = idClass).first():
                return sendResponse(400, 1160, {"message": "Wrong idClass"}, "error")   
        else:
            idClass = None

        newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = generate_password_hash(password), profilePicture = None, email = email, idClass = idClass)

        db.session.add(newUser)
        db.session.commit()

        return sendResponse(201,1171,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role, "profilePicture": newUser.profilePicture,"email": newUser.email, "idClass": newUser.idClass}}, "success")
    
    except:
        #must get it working
        users = request.files.get("jsonFile")
        if not users.filename.rsplit(".", 1)[1].lower() in addUser_extensions:
            return sendResponse(400, 1180, {"message": "Wrong file format"}, "error")
        try:
            for userData in json.load(users):
                data = request.get_json()
                name = data.get("name", None)
                surname = data.get("surname", None)
                abbreviation = data.get("abbreviation", None)
                role = data.get("role", None)
                email = data.get("email", None)
                password = data.get("password", None)
                idClass = data.get("idClass", None)

                if not name or not surname or not role or not password or len(password) < 5 or not email or not re.match(email_regex, email) or User.query.filter_by(email = email).first():
                    return sendResponse (400, 1190, {"message": "Wrong user format"}, "error")
                if abbreviation:
                    if User.query.filter_by(abbreviation = abbreviation.upper()).first():
                        return sendResponse (400, 1200, {"message": "Wrong user format"}, "error")
                    if len(abbreviation) > 4:
                        return sendResponse (400, 1210, {"message": "Wrong user format"}, "error")
                else:
                    abbreviation = None
                if idClass:
                    if not Class.query.filter_by(id = idClass).first():
                        return sendResponse (400, 1220, {"message": "Wrong user format"}, "error")
                else:
                    idClass = None

                newUser = User(name = name, surname = surname, abbreviation = abbreviation.upper(), role = role, password = generate_password_hash(password), profilePicture = None, email = email, idClass = idClass)

                db.session.add(newUser)
            db.session.commit()
        except:
            return sendResponse(400, 1230, {"message": "Something wrong in json"}, "error")
        return sendResponse (201, 1241, {"message": "All users created successfuly"}, "success")

@user_bp.route("/user/update", methods = ["PUT"])
@flask_login.login_required
@checkFileSize(2*1024*1024)
def update():
    #gets data (json)
    name = request.form.get("name", None)
    surname = request.form.get("surname", None)
    abbreviation = request.form.get("abbreviation", None)
    role = request.form.get("role", None)
    email = request.form.get("email", None)
    idClass = request.form.get("idClass", None)
    idUser = request.form.get("idUser", None)
    
    #gets profile picture
    profilePicture = request.files.get("profilePicture", None)
    user = flask_login.current_user

    #checks if there is id for user
    if not idUser:
        if not profilePicture:
            return sendResponse(400, 2010, {"message": "Nothing entered to change"}, "error")
        if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
            return sendResponse(400, 2020, {"message": "Wrong file format"}, "error")
        pfp(pfp_path, user, profilePicture)
        
        db.session.commit()

        return sendResponse(200, 2031, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")
    else:
        if not str(user.role).lower() == "admin":
            return sendResponse(400, 2040, {"message": "No permission for that"}, "error")
        if not name and not surname and not abbreviation and not role and not profilePicture and not email and not idClass:
            return sendResponse(400, 2050, {"message": "Nothing entered to change"}, "error")

        secondUser = User.query.filter_by(id = idUser).first()

        if not secondUser:
            return sendResponse(400, 2060, {"message": "Wrong user id"}, "error")
        if name:
            secondUser.name = name  
        if surname:
            secondUser.surname = surname
        if abbreviation:
            if User.query.filter_by(abbreviation = abbreviation).first() and User.query.filter_by(abbreviation = abbreviation).first() != secondUser:
                return sendResponse(400, 2070, {"message": "Abbreviation is already in use"}, "error")
            if len(str(abbreviation)) > 4:
                return sendResponse(400, 2080, {"message": "Abbreviation is too long"}, "error")
            secondUser.abbreviation = abbreviation
        if role:
            secondUser.role = role
        if email:
            if not re.match(email_regex, email):
                return sendResponse(400, 2090, {"message": "Wrong email format"}, "error")
            if User.query.filter_by(email = email).first() and User.query.filter_by(email = email).first() != secondUser:
                return sendResponse(400, 2100, {"message": "Email is already in use"}, "error")
            if len(email) > 255:
                return sendResponse(400, 2110, {"message": "Email too long"}, "error")
            secondUser.email = email
        if idClass:
            if not Class.query.filter_by(id = idClass).first():
                return sendResponse(400, 2120, {"message": "Wrong idClass"}, "error")
            secondUser.idClass = idClass
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return sendResponse(400, 2130, {"message": "Wrong file format"}, "error")
            pfp(pfp_path, secondUser, profilePicture)            

        db.session.commit()

        return sendResponse(200, 2141, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role, "profilePicture": secondUser.profilePicture, "email": secondUser.email, "idClass": secondUser.idClass}}, "success")
        
@user_bp.route("/user/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force = True)
    idUser = data.get("idUser", None)
    goodIds = []
    badIds = []

    if not flask_login.current_user.role == "admin":
        return sendResponse(400, 3010, {"message": "No permission for that"}, "error")
    if not idUser:
        return sendResponse(400, 3020, {"message": "No idUser"}, "error")
    try:
        id = int(idUser)
        try:
            delUser = User.query.filter_by(id = id).first()
            db.session.delete(delUser)
            goodIds.append(id)
        except:
            badIds.append(id)
    except:
        for id in idUser:
            try:
                delUser = User.query.filter_by(id = id).first()
                db.session.delete(delUser)
                goodIds.append(id)
            except:
                badIds.append(id)

    db.session.commit()

    return sendResponse(200, 3031, {"deletedIds": goodIds, "notdeletedIds": badIds}, "success")

@user_bp.route("/user/update/password", methods = ["PUT"])
@flask_login.login_required
def passwordReset():
    data = request.get_json(force = True)
    oldPassword = data.get("oldPassword", None)
    newPassword = data.get("newPassword", None)

    if not oldPassword:
        return sendResponse(400, 11010, {"message": "Old password not entered"}, "error")
    if not newPassword:
        return sendResponse(400, 11020, {"message": "New password not entered"}, "error")
    if not check_password_hash(flask_login.current_user.password, oldPassword):
        return sendResponse(400, 11030, {"message": "Wrong password"}, "error")
    if len(str(newPassword)) < 5:
        return sendResponse(400, 11040, {"message": "Password is too short"}, "error")
    
    flask_login.current_user.password = generate_password_hash(newPassword)
    db.session.commit()

    return sendResponse(200, 11051, {"message": "Password changed successfuly"}, "success")

@user_bp.route("/user/password/new", methods = ["POST"])
def passwordRes():
    data = request.get_json(force = True)
    email = data.get("email", None)
    
    if not email:
        return sendResponse(400, 12010, {"message": "Email is missing"}, "error")
    if not re.match(email_regex, email):
        return sendResponse(400, 12020, {"message": "Wrong email format"}, "error")
    if not User.query.filter_by(email = email).first():
        return sendResponse(400, 12030, {"message": "No user with that email addres"}, "error")
    
    token = flask_jwt_extended.create_access_token(fresh = True, identity = email, expires_delta= datetime.timedelta(hours = 1),additional_claims = {"email": email})
    link = "http://89.203.248.163/password/forget/reset?token=" + token
    name = User.query.filter_by(email = email).first().name + " " + User.query.filter_by(email = email).first().surname
    html = emailResetPasswordTemplate(name, link)
    text = "Pro resetování hesla zkopírujte tento odkaz: " + link
    sendEmail(email, "Password reset", html, text)

    return sendResponse(200, 12041, {"message": "Token created successfuly and send to email"}, "success")

@user_bp.route("/user/password/verify", methods = ["POST"])
def passwordVerify():
    data = request.get_json(force = True)
    token = data.get("token", None)

    if not token:
        return sendResponse(400, 13010, {"message": "Token is missing"}, "error")
    
    decoded_token = flask_jwt_extended.decode_token(token)

    return sendResponse(200, 13021, {"message": "Verified successfuly", "email":decoded_token["email"]}, "success")

@user_bp.route("/user/password/reset", methods = ["POST"])
def passwordNew():
    data = request.get_json(force=True)
    email = data.get("email", None)
    newPassword = data.get("newPassword", None)

    if not re.match(email_regex, email):
        return sendResponse(400, 14010, {"message": "Wrong email format"}, "error")
    user = User.query.filter_by(email = email).first()

    if not user:
        return sendResponse(400, 14020, {"message": "Wrong email"}, "error")
    if not newPassword:
        return sendResponse(400, 14030, {"message": "Password missing"}, "error")
    if len(str(newPassword)) < 5:
        return sendResponse(400, 14040, {"message": "Password too short"}, "error")
    
    user.password = generate_password_hash(newPassword)
    db.session.commit()
    
    return sendResponse(200, 14051, {"message": "Password reseted successfuly"}, "success")

def getUserById(id):
    user = User.query.filter_by(id = id).first()
    
    if not user:
        return sendResponse(400, "U18010", {"message": "User not found"}, "error")
    
    return sendResponse(200, "U18021", {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")

def getUserByEmail(email):
    if not re.match(email_regex, email):
        return sendResponse(400, "U19010", {"message": "Wrong email format"}, "error")
    
    user = User.query.filter_by(email = email).first()
    
    if not user:
        return sendResponse(400, "U19020", {"message": "User not found"}, "error")
    
    return sendResponse(200, "U19031", {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")

def getUsersByRole(role):
    users = User.query.filter_by(role = role)
    all_users = []

    for user in users:
        all_users.append({"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass})
    if not all_users:
        return sendResponse(400, "U20010", {"message": "Users not found"}, "error")
    
    return sendResponse(200, "U20021", {"message": "Users found", "users": all_users}, "success")

def getUsersByIdClass(idClass):
    users = User.query.filter_by(idClass = idClass)
    all_users = []

    for user in users:
        all_users.append({"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass})
    if not all_users:
        return sendResponse(400, "U21010", {"message": "Users not found"}, "error")
    
    return sendResponse(200, "U21021", {"message": "Users found", "users": all_users}, "success")