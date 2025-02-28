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
        return sendResponse(400, 11, {"message": "No permission for that"}, "error")
    
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
            return sendResponse(400, 3, {"message": "Name is not entered"}, "error")
        if not surname:
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
        if idClass:
            if not Class.query.filter_by(id = idClass).first():
                return sendResponse(400, 7, {"message": "Wrong idClass"}, "error")   
        else:
            idClass = None

        newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = role, password = generate_password_hash(password), profilePicture = None, email = email, idClass = idClass)

        db.session.add(newUser)
        db.session.commit()
        
        encoded_file = encode_file(pfp_path + newUser.profilePicture)

        return sendResponse(201,8,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role, "profilePicture": encoded_file,"email": newUser.email, "idClass": newUser.idClass}}, "success")
    
    except:
        #must get it working
        users = request.files.get("jsonFile")
        if not users.filename.rsplit(".", 1)[1].lower() in addUser_extensions:
            return sendResponse(400, 7, {"message": "Wrong file format"}, "error")
        data = json.load(users)
        return sendResponse(400, 7, {"message": "uhr"}, "error")

@user_bp.route("/user/update", methods = ["POST"])
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
            return sendResponse(400, 10, {"message": "Nothing entered to change"}, "error")
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return sendResponse(400, 7, {"message": "Wrong file format"}, "error")
            pfp(pfp_path, user, profilePicture)

        if password:
            if len(str(password)) < 5:
                return  sendResponse(400, 7, {"message": "Password is too short"}, "error")
            password = generate_password_hash(password)
            user.password = password

        db.session.commit()
        return sendResponse(200, 12, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": user.idClass}}, "success")
    else:
        if not str(user.role).lower() == "admin":
            return sendResponse(400, 11, {"message": "No permission for that"}, "error")
        if not name and not surname and not abbreviation and not role and not profilePicture and not email and not password and not idClass:
            return sendResponse(400, 10, {"message": "Nothing entered to change"}, "error")

        secondUser = User.query.filter_by(id = idUser).first()
        if not secondUser:
            return sendResponse(400, 11, {"message": "Wrong user id"}, "error")
        if name:
            secondUser.name = name  
        if surname:
            secondUser.surname = surname
        if abbreviation:
            secondUser.abbreviation = abbreviation
        if role:
            secondUser.role = role
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return sendResponse(400, 7, {"message": "Wrong file format"}, "error")
            pfp(pfp_path, secondUser, profilePicture)
        if email:
            if not re.match(email_regex, email):
                return sendResponse(400, 9, {"message": "Wrong email format"}, "error")
            secondUser.email = email
        if password:
            if len(str(password)) < 5:
                return sendResponse(400, 7, {"message": "Password is too short"}, "error")
            secondUser.password = generate_password_hash(password)
        if idClass:
            if not Class.query.filter_by(id = idClass).first():
                return sendResponse(400, 7, {"message": "Wrong idClass"}, "error")
            secondUser.idClass = idClass            

        db.session.commit()

        return sendResponse(200, 12, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role, "profilePicture": secondUser.profilePicture, "email": secondUser.email, "idClass": secondUser.idClass}}, "success")
        
@user_bp.route("/user/delete", methods = ["POST"])
@flask_login.login_required
def delete():
    data = request.get_json(force = True)
    idUser = data["idUser"]
    goodIds = []
    badIds = []

    if not flask_login.current_user.role == "admin":
        return sendResponse(400, 11, {"message": "No permission for that"}, "error")
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
    