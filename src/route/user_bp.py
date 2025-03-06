import flask_login
import re
import json
from src.utils.pfp import pfp
from src.models.Class import Class
from src.utils.response import sendResponse
from src.utils.encodeFile import encode_file
from werkzeug.security import generate_password_hash
from flask import request, Blueprint
from app import db
from src.models.User import User

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
        name = data["name"]
        surname = data["surname"]
        abbreviation = data["abbreviation"]
        role = data["role"]
        email = data["email"]
        password = data["password"]
        idClass = data["idClass"]

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
        if len(str(password)) < 5:
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
            if User.query.filter_by(abbreviation = abbreviation).first():
                return sendResponse(400, 1140, {"message": "Abbreviation is already in use"}, "error")
            if len(str(abbreviation)) > 4:
                return sendResponse(400, 1150, {"message": "Abbreviation is too long"}, "error")
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
        
        encoded_file = encode_file(pfp_path + newUser.profilePicture)

        return sendResponse(201,1171,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role, "profilePicture": encoded_file,"email": newUser.email, "idClass": newUser.idClass}}, "success")
    
    except:
        #must get it working
        users = request.files.get("jsonFile")
        if not users.filename.rsplit(".", 1)[1].lower() in addUser_extensions:
            return sendResponse(400, 1140, {"message": "Wrong file format"}, "error")
        try:
            for userData in json.load(users):
                if not userData["name"] or not userData["surname"] or not userData["role"] or not userData["password"] or len(str(userData["password"])) < 5 or not userData["email"] or not re.match(email_regex, userData["email"]) or User.query.filter_by(email = userData["email"]).first():
                    return sendResponse (400, 1150, {"message": "Wrong user format"}, "error")
                if userData["abbreviation"]:
                    if User.query.filter_by(abbreviation = userData["abbreviation"]).first():
                        return sendResponse (400, 1160, {"message": "Wrong user format"}, "error")
                    if len(str(userData["abbreviation"])) > 4:
                        return sendResponse (400, 1170, {"message": "Wrong user format"}, "error")
                else:
                    userData["abbreviation"] = None
                if userData["idClass"]:
                    if not Class.query.filter_by(id = userData["idClass"]).first():
                        return sendResponse (400, 1180, {"message": "Wrong user format"}, "error")
                else:
                    userData["idClass"] = None

                newUser = User(name = userData["name"], surname = userData["surname"], abbreviation = userData["abbreviation"], role = userData["role"], password = generate_password_hash(userData["password"]), profilePicture = None, email = userData["email"], idClass = userData["idClass"])

                db.session.add(newUser)
            db.session.commit()
        except:
            return sendResponse(400, 1190, {"message": "Wrong format in json????"}, "error")
        return sendResponse (201, 1201, {"message": "All users created succesfuly"}, "succes")

@user_bp.route("/user/update", methods = ["PUT"])
@flask_login.login_required
def update():
    #gets data (json)
    name = request.form.get("name")
    surname = request.form.get("surname")
    abbreviation = request.form.get("abbreviation")
    role = request.form.get("role")
    email = request.form.get("email")
    password = request.form.get("password")
    idClass = request.form.get("idClass")
    idUser = request.form.get("idUser")
    
    #gets profile picture
    profilePicture = request.files.get("profilePicture")
    user = flask_login.current_user

    #checks if there is id for user
    if not idUser:
        if not profilePicture and not password:
            return sendResponse(400, 2010, {"message": "Nothing entered to change"}, "error")
        if password:
            if len(str(password)) < 5:
                return  sendResponse(400, 2020, {"message": "Password is too short"}, "error")
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return sendResponse(400, 2030, {"message": "Wrong file format"}, "error")
            pfp(pfp_path, user, profilePicture)
            
            password = generate_password_hash(password)
            user.password = password

        db.session.commit()

        return sendResponse(200, 2041, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")
    else:
        if not str(user.role).lower() == "admin":
            return sendResponse(400, 2050, {"message": "No permission for that"}, "error")
        if not name and not surname and not abbreviation and not role and not profilePicture and not email and not password and not idClass:
            return sendResponse(400, 2060, {"message": "Nothing entered to change"}, "error")

        secondUser = User.query.filter_by(id = idUser).first()

        if not secondUser:
            return sendResponse(400, 2070, {"message": "Wrong user id"}, "error")
        if name:
            secondUser.name = name  
        if surname:
            secondUser.surname = surname
        if abbreviation:
            if User.query.filter_by(abbreviation = abbreviation).first() and User.query.filter_by(abbreviation = abbreviation).first() != secondUser:
                return sendResponse(400, 2080, {"message": "Abbreviation is already in use"}, "error")
            if len(str(abbreviation)) > 4:
                return sendResponse(400, 2090, {"message": "Abbreviation is too long"}, "error")
            secondUser.abbreviation = abbreviation
        if role:
            secondUser.role = role
        if email:
            if not re.match(email_regex, email):
                return sendResponse(400, 2100, {"message": "Wrong email format"}, "error")
            if User.query.filter_by(email = email).first() and User.query.filter_by(email = email).first() != secondUser:
                return sendResponse(400, 2110, {"message": "Email is already in use"}, "error")
            if len(email) > 255:
                return sendResponse(400, 2120, {"message": "Email too long"}, "error")
            secondUser.email = email
        if password:
            if len(str(password)) < 5:
                return sendResponse(400, 2130, {"message": "Password is too short"}, "error")
            secondUser.password = generate_password_hash(password)
        if idClass:
            if not Class.query.filter_by(id = idClass).first():
                return sendResponse(400, 2140, {"message": "Wrong idClass"}, "error")
            secondUser.idClass = idClass
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return sendResponse(400, 2150, {"message": "Wrong file format"}, "error")
            pfp(pfp_path, secondUser, profilePicture)            

        db.session.commit()

        return sendResponse(200, 2161, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role, "profilePicture": secondUser.profilePicture, "email": secondUser.email, "idClass": secondUser.idClass}}, "success")
        
@user_bp.route("/user/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force = True)
    idUser = data["idUser"]
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