import flask_login
import re
import json
import flask_jwt_extended
import datetime
import asyncio
from src.email.templates.resetPassword import emailResetPasswordTemplate
from src.utils.pfp import pfpSave, pfpDelete
from src.utils.allUserClasses import allUserClasses
from src.utils.response import sendResponse
from src.utils.sendEmail import sendEmail
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, Blueprint
from app import db
from src.models.User import User
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.User_Task import User_Task
from src.models.Task_Class import Task_Class
from src.utils.task import taskDeleteSftp
from src.utils.checkFileSize import checkFileSize

user_bp = Blueprint("user", __name__)

email_regex = r"^\S+@\S+\.\S+$"
pfp_path = "/home/filemanager/files/profilePictures/"
task_path = "/home/filemanager/files/tasks/"
pfp_extensions = {"jpg", "png", "jpeg"}
addUser_extensions = {"json"}

@user_bp.route("/user/add", methods = ["POST"])
@flask_login.login_required
@checkFileSize(4*1024*1024)
def add():
    if flask_login.current_user.role != "admin":
        return sendResponse(400, 1010, {"message": "No permission for that"}, "error")
    data = request.get_json()
    
    badIds = []
    goodIds = []
    
    if data:
        name = data.get("name", None)
        surname = data.get("surname", None)
        abbreviation = data.get("abbreviation", None)
        role = data.get("role", None)
        email = data.get("email", None)
        password = str(data.get("password", None))
        idClass = json.loads(data.get("idClass", "[]"))

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
            abbreviation = str(abbreviation).upper()
            if User.query.filter_by(abbreviation = abbreviation).first():
                return sendResponse(400, 1140, {"message": "Abbreviation is already in use"}, "error")
            if len(abbreviation) > 4:
                return sendResponse(400, 1150, {"message": "Abbreviation is too long"}, "error")
        else:
            abbreviation = None

        newUser = User(name = str(name), surname = str(surname), abbreviation = abbreviation, role = str(role).lower(), password = generate_password_hash(password), profilePicture = None, email = email)

        db.session.add(newUser)

        if idClass:
            if newUser.role.lower() == "student":
                for id in idClass:
                    if not Class.query.filter_by(id=id).first():
                        badIds.append(id)
                        continue

                    newUser_Class = User_Class(newUser.id, id)
                    goodIds.append(id)
                    db.session.add(newUser_Class)

        db.session.commit()

        return sendResponse(201,1161,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role, "profilePicture": newUser.profilePicture,"email": newUser.email, "idClass": allUserClasses(newUser.id)}, "goodIds":goodIds, "badIds":badIds}, "success")

    else:
        #must get it working
        users = request.files.get("jsonFile", None)
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
                password = str(data.get("password", None))
                idClass = data.get("idClass", None)

                if not name or not surname or not role or not password or len(password) < 5 or not email or not re.match(email_regex, email) or User.query.filter_by(email = email).first():
                    return sendResponse (400, 1190, {"message": "Wrong user format"}, "error")
                if abbreviation:
                    abbreviation = str(abbreviation).upper()
                    if User.query.filter_by(abbreviation = abbreviation).first():
                        return sendResponse (400, 1200, {"message": "Wrong user format"}, "error")
                    if len(abbreviation) > 4:
                        return sendResponse (400, 1210, {"message": "Wrong user format"}, "error")
                else:
                    abbreviation = None

                newUser = User(name = str(name), surname = str(surname), abbreviation = abbreviation, role = str(role).lower(), password = generate_password_hash(password), profilePicture = None, email = email)
                db.session.add(newUser)

                if idClass:
                    if newUser.role.lower() == "student":
                        for id in idClass:
                            if not Class.query.filter_by(id=id).first():
                                badIds.append(id)
                                continue

                            newUser_Class = User_Class(newUser.id, id)
                            goodIds.append(id)
                            db.session.add(newUser_Class)


            db.session.commit()
        except:
            return sendResponse(400, 1220, {"message": "Something wrong in json"}, "error")
        return sendResponse (201, 1231, {"message": "All users created successfuly"}, "success")

@user_bp.route("/user/update", methods = ["PUT"])
@checkFileSize(2*1024*1024)
@flask_login.login_required
async def update():
    #gets data (json)
    name = request.form.get("name", None)
    surname = request.form.get("surname", None)
    abbreviation = request.form.get("abbreviation", None)
    role = request.form.get("role", None)
    email = request.form.get("email", None)
    idUser = request.form.get("idUser", None)
    idClass = json.loads(request.form.get("idClass", "[]"))
    
    #gets profile picture
    profilePicture = request.files.get("profilePicture", None)
    user = flask_login.current_user
    badIds = []
    goodIds = []

    #checks if there is id for user
    if not idUser:
        if not profilePicture:
            return sendResponse(400, 2010, {"message": "Nothing entered to change"}, "error")
        if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
            return sendResponse(400, 2020, {"message": "Wrong file format"}, "error")
        await pfpSave(pfp_path, user, profilePicture)
        
        db.session.commit()

        return sendResponse(200, 2031, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": allUserClasses(user.id)}}, "success")
    else:
        if not str(user.role).lower() == "admin":
            return sendResponse(400, 2040, {"message": "No permission for that"}, "error")
        if not name and not surname and not abbreviation and not role and not profilePicture and not email and not idClass:
            return sendResponse(400, 2050, {"message": "Nothing entered to change"}, "error")

        secondUser = User.query.filter_by(id = idUser).first()

        if not secondUser:
            return sendResponse(400, 2060, {"message": "Wrong user id"}, "error")
        if name:
            secondUser.name = str(name)  
        if surname:
            secondUser.surname = str(surname)
        if abbreviation:
            if User.query.filter_by(abbreviation = abbreviation).first() and User.query.filter_by(abbreviation = abbreviation).first() != secondUser:
                return sendResponse(400, 2070, {"message": "Abbreviation is already in use"}, "error")
            if len(str(abbreviation)) > 4:
                return sendResponse(400, 2080, {"message": "Abbreviation is too long"}, "error")
            secondUser.abbreviation = str(abbreviation).upper()
        if role:
            secondUser.role = str(role).lower()
        if email:
            if not re.match(email_regex, email):
                return sendResponse(400, 2090, {"message": "Wrong email format"}, "error")
            if User.query.filter_by(email = email).first() and User.query.filter_by(email = email).first() != secondUser:
                return sendResponse(400, 2100, {"message": "Email is already in use"}, "error")
            if len(email) > 255:
                return sendResponse(400, 2110, {"message": "Email too long"}, "error")
            secondUser.email = email
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return sendResponse(400, 2120, {"message": "Wrong file format"}, "error")
            await pfpSave(pfp_path, secondUser, profilePicture)

        if idClass:
            if secondUser.role.lower() == "student":
                for id in allUserClasses(secondUser.id):
                    for task in User_Task.query.filter_by(idUser = secondUser.id):
                        if Task_Class.query.filter_by(idTask = task.idTask, idClass = id).first():
                            db.session.delete(task)
                    db.session.delete(User_Class.query.filter_by(idUser = secondUser.id, idClass = id).first())
                
                for id in idClass:
                    if not Class.query.filter_by(id=id).first():
                        badIds.append(id)
                        continue

                    newUser_Class = User_Class(secondUser.id, id)
                    goodIds.append(id)
                    db.session.add(newUser_Class)     
            else:
                User_class = User_Class.query.filter_by(idUser = secondUser.id)
                for cl in User_class:
                    db.session.delete(cl)

        db.session.commit()

        return sendResponse(200, 2131, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role, "profilePicture": secondUser.profilePicture, "email": secondUser.email, "idClass": allUserClasses(secondUser.id)}, "badIds":badIds, "goodIds":goodIds}, "success")
        
@user_bp.route("/user/delete", methods = ["DELETE"])
@flask_login.login_required
async def delete():
    data = request.get_json(force = True)
    idUser = data.get("idUser", None)
    goodIds = []
    badIds = []

    if not flask_login.current_user.role == "admin":
        return sendResponse(400, 3010, {"message": "No permission for that"}, "error")
    if not idUser:
        return sendResponse(400, 3020, {"message": "No idUser"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]
    for id in idUser:
        if flask_login.current_user.id == id:
            return sendResponse(400, 3030, {"message": "Can not delete yourself"}, "error")
        delUser = User.query.filter_by(id = id).first()

        if delUser:
            cl = User_Class.query.filter_by(idUser = id)
            ta = User_Task.query.filter_by(idUser = id)

            for c in cl:
                db.session.delete(c)
            for t in ta:
                await taskDeleteSftp(task_path + str(t.idTask) + "/", id)
                db.session.delete(t)

            await pfpDelete(pfp_path, delUser)
            db.session.delete(delUser)
            goodIds.append(id)
        else:
            badIds.append(id)
    if not goodIds:
        return sendResponse(400, 3040, {"message": "Nothing deleted"}, "error")

    db.session.commit()

    return sendResponse(200, 3051, {"message":"Successfuly deleted users", "deletedIds": goodIds, "notdeletedIds": badIds}, "success")

@user_bp.route("/user/update/password", methods = ["PUT"])
@flask_login.login_required
def passwordReset():
    data = request.get_json(force = True)
    oldPassword = str(data.get("oldPassword", None))
    newPassword = str(data.get("newPassword", None))

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
    newPassword = str(data.get("newPassword", None))

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

@user_bp.route("/user/get/id", methods = ["GET"])
@flask_login.login_required
def getUserById():
    id = request.args.get("id", None)

    if not id:
        return sendResponse(400, 18010, {"message": "Id not entered"}, "error")

    user = User.query.filter_by(id = id).first()
    
    if not user:
        return sendResponse(400, 18020, {"message": "User not found"}, "error")
    
    return sendResponse(200, 18031, {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": allUserClasses(user.id)}}, "success")

@user_bp.route("/user/get/email", methods = ["GET"])
@flask_login.login_required
def getUserByEmail():
    email = request.args.get("email", None)

    if not email:
        return sendResponse(400, 19010, {"message": "Email not entered"}, "error")
    if not re.match(email_regex, email):
        return sendResponse(400, 19020, {"message": "Wrong email format"}, "error")
    
    user = User.query.filter_by(email = email).first()
    
    if not user:
        return sendResponse(400, 19030, {"message": "User not found"}, "error")
    
    return sendResponse(200, 19041, {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": allUserClasses(user.id)}}, "success")

@user_bp.route("/user/get/role", methods = ["GET"])
@flask_login.login_required
def getUsersByRole():
    role = request.args.get("role", None)
    all_users = []

    if not role:
        return sendResponse(400, 20010, {"message": "Role not entered"}, "error")
    
    users = User.query.filter_by(role = role)

    for user in users:
        all_users.append({"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": allUserClasses(user.id)})
    if not all_users:
        return sendResponse(400, 20020, {"message": "Users not found"}, "error")
    
    return sendResponse(200, 20031, {"message": "Users found", "users": all_users}, "success")

#cestu vymyslíme jindy
@user_bp.route("/user/get/number", methods = ["GET"])
@flask_login.login_required
def getNumberOfUsers():
    number = 0
    users = User.query.all()

    for user in users:
        number += 1

    return sendResponse(200, 24011, {"message": "Number of users", "users": number}, "success")

@user_bp.route("/user/get/roles", methods = ["GET"])
@flask_login.login_required
def getRoles():
    roles = []
    users = User.query.all()

    for user in users:
        role = user.role
        if not role in roles:
            roles.append(role)

    return sendResponse(200, 25011, {"message": "All roles", "roles": roles}, "success")

@user_bp.route("/user/get/currentRole", methods=["GET"])
@flask_login.login_required
def getCurrentRole():
    return sendResponse(200, 21011, {"message": "Current user role", "role":flask_login.current_user.role}, "success")

@user_bp.route("/user/get/noClass", methods =["GET"])
@flask_login.login_required
def getNoClass():
    user = User.query.filter_by(role = "student")
    users = []

    for s in user:
        if not User_Class.query.filter_by(idUser = s.id).first():
            users.append({"id": s.id, "name": s.name, "surname": s.surname, "abbreviation": s.abbreviation, "role": s.role, "profilePicture": s.profilePicture, "email": s.email})

    return sendResponse(200, 40011, {"message": "All students without class", "users": users}, "success")