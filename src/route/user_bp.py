import flask_login
import re
import json
import flask_jwt_extended
import datetime
from src.email.templates.reset_password import email_reset_password_template
from src.utils.pfp import pfp_save, pfp_delete
from src.utils.all_user_classes import all_user_classes
from src.utils.response import send_response
from src.utils.send_email import send_email
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, Blueprint
from app import db, pfp_path, url
from src.models.User import User
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.utils.task import task_delete_sftp
from src.utils.check_file import check_file_size
from src.utils.team import delete_teams_for_task
from src.utils.enums import Role

user_bp = Blueprint("user", __name__)

email_regex = r"^\S+@\S+\.\S+$"
pfp_extensions = {"jpg", "png", "jpeg"}
addUser_extensions = {"json"}

@user_bp.route("/user/add", methods = ["POST"])
@flask_login.login_required
@check_file_size(4*1024*1024)
def add():
    if flask_login.current_user.role != Role.Admin:
        return send_response(400, 1010, {"message": "No permission for that"}, "error")
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
        idClass = data.get("classes", None)
        lastUser = User.query.order_by(User.id.desc()).first()

        if not name:
            return send_response(400, 1020, {"message": "Name is not entered"}, "error")
        if len(name) > 100:
            return send_response(400, 1030, {"message": "Name too long"}, "error")
        if not surname:
            return send_response(400, 1040, {"message": "Surname is not entered"}, "error")
        if len(surname) > 100:
            return send_response(400, 1050, {"message": "Surname too long"}, "error")
        if not role:
            return send_response(400, 1060,{"message": "Role is not entered"}, "error")
        if role not in [r.value for r in Role]:
            return send_response(400, 1070, {"message": "Role not our type"}, "error")
        if not password:
            return send_response(400, 1080, {"message": "Password is not entered"}, "error")
        if len(password) < 5:
            return  send_response(400, 1090, {"message": "Password is too short"}, "error")
        if not email:
            return send_response(400, 1100, {"message": "Email is not entered"}, "error")
        if not re.match(email_regex, email):
            return send_response(400, 1110, {"message": "Wrong email format"}, "error")
        if len(email) > 255:
            return send_response(400, 1120, {"message": "Email too long"}, "error")
        if User.query.filter_by(email = email).first():
            return send_response(400, 1130, {"message": "Email is already in use"}, "error")
        if abbreviation:
            abbreviation = str(abbreviation).upper()
            if User.query.filter_by(abbreviation = abbreviation).first():
                return send_response(400, 1140, {"message": "Abbreviation is already in use"}, "error")
            if len(abbreviation) > 4:
                return send_response(400, 1150, {"message": "Abbreviation is too long"}, "error")
        else:
            abbreviation = None

        newUser = User(name = str(name), surname = str(surname), abbreviation = abbreviation, role = Role(role), password = generate_password_hash(password), profilePicture = None, email = email)

        db.session.add(newUser)

        if idClass:
            if lastUser:
                idUser = lastUser.id + 1
            else:
                idUser = 1

            if role == Role.Student:
                for id in idClass:
                    if not Class.query.filter_by(id=id).first():
                        badIds.append(id)
                        continue

                    newUser_Class = User_Class(idUser, id)
                    goodIds.append(id)
                    db.session.add(newUser_Class)

        db.session.commit()

        return send_response(201,1161,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role.value, "profilePicture": newUser.profilePicture,"email": newUser.email, "idClass": all_user_classes(newUser.id), "createdAt":newUser.createdAt, "updatedAt":newUser.updatedAt}, "goodIds":goodIds, "badIds":badIds}, "success")

    else:
        users = request.files.get("jsonFile", None)
        if not users.filename.rsplit(".", 1)[1].lower() in addUser_extensions:
            return send_response(400, 1180, {"message": "Wrong file format"}, "error")
        try:
            #TODO: potom dodělat
            for userData in json.load(users):
                data = request.get_json()
                name = data.get("name", None)
                surname = data.get("surname", None)
                abbreviation = data.get("abbreviation", None)
                role = data.get("role", None)
                email = data.get("email", None)
                password = str(data.get("password", None))
                idClass = data.get("classes", None)

                if not name or not surname or not role or role not in [r.value for r in Role] or not password or len(password) < 5 or not email or not re.match(email_regex, email) or User.query.filter_by(email = email).first():
                    return send_response (400, 1190, {"message": "Wrong user format"}, "error")
                if abbreviation:
                    abbreviation = str(abbreviation).upper()
                    if User.query.filter_by(abbreviation = abbreviation).first():
                        return send_response (400, 1200, {"message": "Wrong user format"}, "error")
                    if len(abbreviation) > 4:
                        return send_response (400, 1210, {"message": "Wrong user format"}, "error")
                else:
                    abbreviation = None

                newUser = User(name = str(name), surname = str(surname), abbreviation = abbreviation, role = Role(role), password = generate_password_hash(password), profilePicture = None, email = email)
                db.session.add(newUser)
                db.session.commit()
                lastUser = User.query.order_by(User.id.desc()).first()

                if idClass:
                    if str(role).lower() == "student":
                        for id in idClass:
                            if not Class.query.filter_by(id=id).first():
                                badIds.append(id)
                                continue

                            newUser_Class = User_Class(idUser, id)
                            goodIds.append(id)
                            db.session.add(newUser_Class)
                    db.session.commit()
        except:
            return send_response(400, 1220, {"message": "Something wrong in json"}, "error")
        return send_response (201, 1231, {"message": "All users created successfuly"}, "success")

@user_bp.route("/user/update", methods = ["PUT"])
@check_file_size(2*1024*1024)
@flask_login.login_required
async def update():
    #gets data (json)
    name = request.form.get("name", None)
    surname = request.form.get("surname", None)
    abbreviation = request.form.get("abbreviation", None)
    role = request.form.get("role", None)
    email = request.form.get("email", None)
    idUser = request.form.get("idUser", None)
    raw_id_class = request.form.get("idClass", "")
    
    try:
        idClass = json.loads(raw_id_class) if raw_id_class.strip() else []
    except:
        idClass = []

    if not isinstance(idClass, list):
        idClass = [idClass]
    
    #gets profile picture
    profilePicture = request.files.get("profilePicture", None)
    user = flask_login.current_user
    badIds = []
    goodIds = []

    #checks if there is id for user
    if not idUser:
        if not profilePicture:
            return send_response(400, 2010, {"message": "Nothing entered to change"}, "error")
        if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
            return send_response(400, 2020, {"message": "Wrong file format"}, "error")
        await pfp_save(pfp_path, user, profilePicture)

        user.updatedAt = datetime.datetime.now()
        
        db.session.commit()

        return send_response(200, 2031, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt}}, "success")
    else:
        if not user.role == Role.Admin:
            return send_response(400, 2040, {"message": "No permission for that"}, "error")
        if not name and not surname and not abbreviation and not role and not profilePicture and not email and not idClass:
            return send_response(400, 2050, {"message": "Nothing entered to change"}, "error")

        secondUser = User.query.filter_by(id = idUser).first()

        if not secondUser:
            return send_response(400, 2060, {"message": "Wrong user id"}, "error")
        if name:
            secondUser.name = str(name)  
        if surname:
            secondUser.surname = str(surname)
        if abbreviation:
            if User.query.filter_by(abbreviation = abbreviation).first() and User.query.filter_by(abbreviation = abbreviation).first() != secondUser:
                return send_response(400, 2070, {"message": "Abbreviation is already in use"}, "error")
            if len(str(abbreviation)) > 4:
                return send_response(400, 2080, {"message": "Abbreviation is too long"}, "error")
            secondUser.abbreviation = str(abbreviation).upper()
        if role in [r.value for r in Role]:
            secondUser.role = Role(role)
        if email:
            if not re.match(email_regex, email):
                return send_response(400, 2090, {"message": "Wrong email format"}, "error")
            if User.query.filter_by(email = email).first() and User.query.filter_by(email = email).first() != secondUser:
                return send_response(400, 2100, {"message": "Email is already in use"}, "error")
            if len(email) > 255:
                return send_response(400, 2110, {"message": "Email too long"}, "error")
            secondUser.email = email
        if profilePicture:
            if not profilePicture.filename.rsplit(".", 1)[1].lower() in pfp_extensions:
                return send_response(400, 2120, {"message": "Wrong file format"}, "error")
            await pfp_save(pfp_path, secondUser, profilePicture)

        if idClass:
            if secondUser.role == Role.Student:
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

        secondUser.updatedAt = datetime.datetime.now()

        db.session.commit()

        return send_response(200, 2131, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role.value, "profilePicture": secondUser.profilePicture, "email": secondUser.email, "idClass": all_user_classes(secondUser.id), "createdAt":secondUser.createdAt, "updatedAt":secondUser.updatedAt}, "badIds":badIds, "goodIds":goodIds}, "success")
        
@user_bp.route("/user/delete", methods = ["DELETE"])
@flask_login.login_required
async def delete():
    data = request.get_json(force = True)
    idUser = data.get("idUser", None)
    goodIds = []
    badIds = []

    if not flask_login.current_user.role == Role.Admin:
        return send_response(400, 3010, {"message": "No permission for that"}, "error")
    if not idUser:
        return send_response(400, 3020, {"message": "No idUser"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]
    for id in idUser:
        if flask_login.current_user.id == id:
            return send_response(400, 3030, {"message": "Can not delete yourself"}, "error")
        delUser = User.query.filter_by(id = id).first()

        if delUser:
            cl = User_Class.query.filter_by(idUser = id)
            ta = User_Team.query.filter_by(idUser = id)
            tas = Task.query.filter_by(guarantor = id)

            for t in ta:
                db.session.delete(t)
            for c in cl:
                db.session.delete(c)
            for task in tas:
                await delete_teams_for_task(task.id)
                await task_delete_sftp(task.id)
                db.session.delete(task)
            db.session.commit()

            await pfp_delete(pfp_path, delUser)
            db.session.delete(delUser)
            goodIds.append(id)
        else:
            badIds.append(id)
    if not goodIds:
        return send_response(400, 3040, {"message": "Nothing deleted"}, "error")

    db.session.commit()

    return send_response(200, 3051, {"message":"Successfuly deleted users", "deletedIds": goodIds, "notdeletedIds": badIds}, "success")

@user_bp.route("/user/update/password", methods = ["PUT"])
@flask_login.login_required
def password_reset():
    data = request.get_json(force = True)
    oldPassword = str(data.get("oldPassword", None))
    newPassword = str(data.get("newPassword", None))

    if not oldPassword:
        return send_response(400, 11010, {"message": "Old password not entered"}, "error")
    if not newPassword:
        return send_response(400, 11020, {"message": "New password not entered"}, "error")
    if not check_password_hash(flask_login.current_user.password, oldPassword):
        return send_response(400, 11030, {"message": "Wrong password"}, "error")
    if len(str(newPassword)) < 5:
        return send_response(400, 11040, {"message": "Password is too short"}, "error")
    
    flask_login.current_user.password = generate_password_hash(newPassword)
    db.session.commit()

    return send_response(200, 11051, {"message": "Password changed successfuly"}, "success")

@user_bp.route("/user/password/new", methods = ["POST"])
def password_res():
    data = request.get_json(force = True)
    email = data.get("email", None)
    
    if not email:
        return send_response(400, 12010, {"message": "Email is missing"}, "error")
    if not re.match(email_regex, email):
        return send_response(400, 12020, {"message": "Wrong email format"}, "error")
    if not User.query.filter_by(email = email).first():
        return send_response(400, 12030, {"message": "No user with that email addres"}, "error")
    
    token = flask_jwt_extended.create_access_token(fresh = True, identity = email, expires_delta= datetime.timedelta(hours = 1),additional_claims = {"email": email})
    link = url + "/password/forget/reset?token=" + token
    name = User.query.filter_by(email = email).first().name + " " + User.query.filter_by(email = email).first().surname
    html = email_reset_password_template(name, link)
    text = "Pro resetování hesla zkopírujte tento odkaz: " + link
    send_email(email, "Password reset", html, text)

    return send_response(200, 12041, {"message": "Token created successfuly and send to email"}, "success")

@user_bp.route("/user/password/verify", methods = ["POST"])
def password_verify():
    data = request.get_json(force = True)
    token = data.get("token", None)

    if not token:
        return send_response(400, 13010, {"message": "Token is missing"}, "error")
    
    decoded_token = flask_jwt_extended.decode_token(token)

    return send_response(200, 13021, {"message": "Verified successfuly", "email":decoded_token["email"]}, "success")

@user_bp.route("/user/password/reset", methods = ["POST"])
def password_new():
    data = request.get_json(force=True)
    email = data.get("email", None)
    newPassword = str(data.get("newPassword", None))

    if not re.match(email_regex, email):
        return send_response(400, 14010, {"message": "Wrong email format"}, "error")
    user = User.query.filter_by(email = email).first()

    if not user:
        return send_response(400, 14020, {"message": "Wrong email"}, "error")
    if not newPassword:
        return send_response(400, 14030, {"message": "Password missing"}, "error")
    if len(str(newPassword)) < 5:
        return send_response(400, 14040, {"message": "Password too short"}, "error")
    
    user.password = generate_password_hash(newPassword)
    db.session.commit()
    
    return send_response(200, 14051, {"message": "Password reseted successfuly"}, "success")

@user_bp.route("/user/get/id", methods = ["GET"])
@flask_login.login_required
def get_by_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 18010, {"message": "Id not entered"}, "error")

    user = User.query.filter_by(id = id).first()
    
    if not user:
        return send_response(400, 18020, {"message": "User not found"}, "error")
    
    return send_response(200, 18031, {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt}}, "success")

@user_bp.route("/user/get/email", methods = ["GET"])
@flask_login.login_required
def get_by_email():
    email = request.args.get("email", None)

    if not email:
        return send_response(400, 19010, {"message": "Email not entered"}, "error")
    if not re.match(email_regex, email):
        return send_response(400, 19020, {"message": "Wrong email format"}, "error")
    
    user = User.query.filter_by(email = email).first()
    
    if not user:
        return send_response(400, 19030, {"message": "User not found"}, "error")
    
    return send_response(200, 19041, {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt}}, "success")

@user_bp.route("/user/get/role", methods = ["GET"])
@flask_login.login_required
def get_by_role():
    role = request.args.get("role", None)
    all_users = []

    if not role:
        return send_response(400, 20010, {"message": "Role not entered"}, "error")
    
    users = User.query.filter_by(role = role)

    for user in users:
        all_users.append({"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt})
    if not all_users:
        return send_response(400, 20020, {"message": "Users not found"}, "error")
    
    return send_response(200, 20031, {"message": "Users found", "users": all_users}, "success")

@user_bp.route("/user/get/number", methods = ["GET"])
@flask_login.login_required
def get_of_users():
    number = 0
    users = User.query.all()

    for user in users:
        number += 1

    return send_response(200, 24011, {"message": "Number of users", "users": number}, "success")

@user_bp.route("/user/get/roles", methods = ["GET"])
@flask_login.login_required
def get_roles():
    roles = []
    users = User.query.all()

    for user in users:
        role = user.role
        if not role in roles:
            roles.append(role)

    return send_response(200, 25011, {"message": "All roles", "roles": roles}, "success")

@user_bp.route("/user/get/currentRole", methods=["GET"])
@flask_login.login_required
def get_current_role():
    return send_response(200, 21011, {"message": "Current user role", "role":flask_login.current_user.role}, "success")

@user_bp.route("/user/get/noClass", methods =["GET"])
@flask_login.login_required
def get_no_class():
    user = User.query.filter_by(role = "student")
    users = []

    for s in user:
        if not User_Class.query.filter_by(idUser = s.id).first():
            users.append({"id": s.id, "name": s.name, "surname": s.surname, "abbreviation": s.abbreviation, "role": s.role.value, "profilePicture": s.profilePicture, "email": s.email, "createdAt":s.createdAt, "updatedAt":s.updatedAt})

    return send_response(200, 40011, {"message": "All students without class", "users": users}, "success")

@user_bp.route("/user/get/count/by-role", methods=["GET"])
@flask_login.login_required
def get_count_by_role():
    role = request.args.get("role", None)

    if not role:
        return send_response(400, 48010, {"message": "Role not entered"}, "error")

    count = User.query.filter_by(role=role).count()

    return send_response(200, 48021, {"message": "User count found", "count": count}, "success")

@user_bp.route("/user/logged/data", methods = ["GET"])
@flask_login.login_required
def get_logged_user_data():
    user = flask_login.current_user

    return send_response(200, 50011, {"message": "Logged user data", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt}}, "success")