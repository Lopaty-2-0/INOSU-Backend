import flask_login
import re
import json
import flask_jwt_extended
import datetime
from src.email.templates.reset_password import email_reset_password_template
from src.utils.pfp import pfp_save, pfp_delete, pfp_check
from src.utils.all_user_classes import all_user_classes
from src.utils.response import send_response
from src.utils.send_email import send_email
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, Blueprint
from app import db, url, max_INT
from src.models.User import User
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.Conversation import Conversation
from src.utils.archive_conversation import cancel_archive_conversation
from src.models.Message import Message
from src.models.Task import Task
from src.models.Maturita_Task import Maturita_Task
from src.utils.task import delete_upload_task
from src.utils.check_file import check_file_size
from src.utils.team import delete_teams_for_task
from src.utils.enums import Role, Type
from src.utils.paging import user_paging
from sqlalchemy import or_

user_bp = Blueprint("user", __name__)

email_regex = r"^\S+@\S+\.\S+$"
pfp_extensions = {"jpg", "png", "jpeg"}
addUser_extensions = {"json"}

@user_bp.route("/user/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 1010, {"message": "No permission for that"}, "error")
    data = request.get_json()
    
    badIds = []
    goodIds = []
    
    name = data.get("name", None)
    surname = data.get("surname", None)
    abbreviation = data.get("abbreviation", None)
    role = data.get("role", None)
    email = data.get("email", None)
    password = data.get("password", None)
    idClass = data.get("classes", None)

    if not name:
        return send_response(400, 1020, {"message": "Name is not entered"}, "error")
    if len((name)) > 100:
        return send_response(400, 1030, {"message": "Name too long"}, "error")
    if not surname:
        return send_response(400, 1040, {"message": "Surname is not entered"}, "error")
    if len((surname)) > 100:
        return send_response(400, 1050, {"message": "Surname too long"}, "error")
    if not role:
        return send_response(400, 1060,{"message": "Role is not entered"}, "error")
    if role not in [r.value for r in Role]:
        return send_response(400, 1070, {"message": "Role not our type"}, "error")
    if not password:
        return send_response(400, 1080, {"message": "Password is not entered"}, "error")
    
    password = str(password)
    email = str(email)
    name = str(name)
    surname = str(surname)
    

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
        abbreviation = str(abbreviation)
        abbreviation = (abbreviation).upper()
        if User.query.filter_by(abbreviation = abbreviation).first():
            return send_response(400, 1140, {"message": "Abbreviation is already in use"}, "error")
        if len(abbreviation) > 4:
            return send_response(400, 1150, {"message": "Abbreviation is too long"}, "error")
    else:
        abbreviation = None

    newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = Role(role), password = generate_password_hash(password), profilePicture = None, email = email)

    db.session.add(newUser)
    db.session.commit()

    if idClass:
        if not isinstance(idClass, list):
            idClass = [idClass]
        idUser = newUser.id

        if newUser.role == Role.Student:
            for id in idClass:
                try:
                    id = int(id)
                except:
                    badIds.append(id)
                    continue

                if id > max_INT or id <= 0 or not Class.query.filter_by(id=id).first():
                    badIds.append(id)
                    continue

                newUserClass = User_Class(idUser, id)
                goodIds.append(id)
                db.session.add(newUserClass)
            db.session.commit()

    return send_response(201,1161,{"message" : "User created successfuly", "user": {"id": newUser.id, "name": newUser.name, "surname": newUser.surname, "abbreviation": newUser.abbreviation, "role": newUser.role.value, "profilePicture": newUser.profilePicture,"email": newUser.email, "idClass": all_user_classes(newUser.id), "reminders":newUser.reminders}, "goodIds": goodIds, "badIds":badIds}, "success")
  
@user_bp.route("/user/add/file", methods = ["POST"])
@flask_login.login_required
def add_file():
    badUsers = 0
    allUsers = 0
    badIds = []
    goodIds = []
    users = request.files.get("jsonFile", None)
    size = request.form.get("size", None)

    response = check_file_size(4*1024*1024, size)

    if response:
        return response
    
    file_content = users.read().decode("utf-8").strip()

    if not file_content:
        return send_response(400, 50010, {"message": "File is empty"}, "error")

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError:
        return send_response(400, 50020, {"message": "Invalid JSON format"}, "error")
    
    for userData in data.get("users", []):
        name = userData.get("name", None)
        surname = userData.get("surname", None)
        abbreviation = userData.get("abbreviation", None)
        role = userData.get("role", None)
        email = userData.get("email", None)
        password = (userData.get("password", None))
        idClass = userData.get("classes", None)

        if not name or not surname or not role or not password or not email:
            badUsers += 1
            continue

        password = str(password)
        email = str(email)
        name = str(name)
        surname = str(surname)   

        if len(name) > 100 or len(surname) > 100 or role not in [r.value for r in Role] or len(password) < 5 or len(email) > 255 or not re.match(email_regex, email) or User.query.filter_by(email = email).first():
            badUsers += 1
            continue
        if abbreviation:
            abbreviation = str(abbreviation)
            abbreviation = (abbreviation).upper()
            if User.query.filter_by(abbreviation = abbreviation).first():
                badUsers += 1
                continue
            if len(abbreviation) > 4:
                badUsers += 1
                continue
        else:
            abbreviation = None
        allUsers += 1

        newUser = User(name = name, surname = surname, abbreviation = abbreviation, role = Role(role), password = generate_password_hash(password), profilePicture = None, email = email)
        db.session.add(newUser)
        db.session.commit()

        if idClass:
            if newUser.role == Role.Student:
                for id in idClass:
                    try:
                        id = int(id)
                    except:
                        badIds.append(id)
                        continue
                    if id > max_INT or id <= 0 or not Class.query.filter_by(id=id).first():
                        badIds.append(id)
                        continue

                    newUserClass = User_Class(newUser.id, id)
                    goodIds.append(id)
                    db.session.add(newUserClass)
            db.session.commit()
    
    if allUsers <= badUsers:
        return send_response (400, 50030, {"message": "No users created"}, "error") 
            
    return send_response (201, 50041, {"message": "All users created successfuly"}, "success")

@user_bp.route("/user/update", methods = ["PUT"])
@flask_login.login_required
def update():
    #gets data (json)
    data = request.get_json(force=True)
    name = data.get("name", None)
    surname = data.get("surname", None)
    abbreviation = data.get("abbreviation", None)
    role = data.get("role", None)
    email = data.get("email", None)
    idUser = data.get("idUser", None)
    reminders = data.get("reminders", None)
    rawIdClass = data.get("idClass", "")
    profilePicture = data.get("profilePicture", None)
    size = data.get("size", None)
    uploadUrl = None
    fileName = None
    
    try:
        idClass = json.loads(rawIdClass) if rawIdClass.strip() else None
    except:
        idClass = None

    user = flask_login.current_user
    badIds = []
    goodIds = []

    if profilePicture:
        pictureResponse = check_file_size(2*1024*1024, size)

        if pictureResponse:
            return pictureResponse
        
    #checks if there is id for user
    if not idUser:
        if not profilePicture and not isinstance(reminders, bool):
            return send_response(400, 2010, {"message": "Nothing entered to change"}, "error")
        if profilePicture:
            if len(profilePicture.rsplit(".", 1)) < 2 or not profilePicture.rsplit(".", 1)[1].lower() in pfp_extensions:
                return send_response(400, 2020, {"message": "Wrong file format"}, "error")

            fileName, uploadUrl = pfp_save(profilePicture)

        if isinstance(reminders, bool):
            user.reminders = reminders

        user.updatedAt = datetime.datetime.now(datetime.timezone.utc)
        
        db.session.commit()

        return send_response(200, 2031, {"message": "User changed successfuly", "user":{"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": fileName, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}, "uploadUrl":uploadUrl}, "success")

    if not user.role == Role.Admin:
        return send_response(400, 2040, {"message": "No permission for that"}, "error")
    
    try:
        idUser = int(idUser)
    except:
            return send_response(400, 2050, {"message": "IdUser not integer"}, "error")
    
    if idUser > max_INT or idUser <= 0:
        return send_response(400, 2060, {"message": "IdUser not valid"}, "error")

    secondUser = User.query.filter_by(id = idUser).first()

    if not secondUser:
        return send_response(400, 2070, {"message": "Wrong user id"}, "error")
    if name:
        name = str(name)
        if len(name) > 255:
            return send_response(400, 2080, {"message": "Name too long"}, "error")
        secondUser.name = (name)  
    if surname:
        surname = str(surname)
        if len(surname) > 255:
            return send_response(400, 2090, {"message": "Surname too long"}, "error")
        secondUser.surname = (surname)
    if abbreviation:
        abbreviation = str(abbreviation)
        if User.query.filter_by(abbreviation = abbreviation).first() and User.query.filter_by(abbreviation = abbreviation).first() != secondUser:
            return send_response(400, 2100, {"message": "Abbreviation is already in use"}, "error")
        if len(abbreviation) > 4:
            return send_response(400, 2110, {"message": "Abbreviation is too long"}, "error")
        secondUser.abbreviation = abbreviation.upper()
    if role in [r.value for r in Role]:
        secondUser.role = Role(role)
        if Role(role)!= Role.Student:
            User_class = User_Class.query.filter_by(idUser = secondUser.id)
            for cl in User_class:
                db.session.delete(cl)
    if email:
        email = str(email)
        if not re.match(email_regex, email):
            return send_response(400, 2120, {"message": "Wrong email format"}, "error")
        if User.query.filter_by(email = email).first() and User.query.filter_by(email = email).first() != secondUser:
            return send_response(400, 2130, {"message": "Email is already in use"}, "error")
        if len(email) > 255:
            return send_response(400, 2140, {"message": "Email too long"}, "error")
        secondUser.email = email
    if profilePicture:
        if len(profilePicture.rsplit(".", 1)) < 2 or not profilePicture.rsplit(".", 1)[1].lower() in pfp_extensions:
            return send_response(400, 2150, {"message": "Wrong file format"}, "error")

        fileName, uploadUrl = pfp_save(profilePicture)

    if isinstance(idClass, list):    
        UserClass = User_Class.query.filter_by(idUser = secondUser.id)
        for cl in UserClass:
            db.session.delete(cl)
    
        if secondUser.role == Role.Student:
            for id in idClass:
                try:
                    id = int(id)
                except:
                    badIds.append(id)
                    continue
                if id > max_INT or id <= 0 or not Class.query.filter_by(id=id).first() or User_Class.query.filter_by(idUser = secondUser.id, idClass = id).first():
                    badIds.append(id)
                    continue

                newUserClass = User_Class(secondUser.id, id)
                goodIds.append(id)
                db.session.add(newUserClass)

    secondUser.updatedAt = datetime.datetime.now(datetime.timezone.utc)

    db.session.commit()

    return send_response(200, 2161, {"message": "User changed successfuly", "user":{"id": secondUser.id, "name": secondUser.name, "surname": secondUser.surname, "abbreviation": secondUser.abbreviation, "role": secondUser.role.value, "profilePicture": fileName, "email": secondUser.email, "idClass": all_user_classes(secondUser.id), "createdAt":secondUser.createdAt, "updatedAt":secondUser.updatedAt, "reminders":secondUser.reminders}, "badIds":badIds, "goodIds":goodIds, "uploadUrl":uploadUrl}, "success")
    
@user_bp.route("/user/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force = True)
    idUser = data.get("idUser", None)
    goodIds = []
    badIds = []

    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 3010, {"message": "No permission for that"}, "error")
    if not idUser:
        return send_response(400, 3020, {"message": "No idUser"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]
    for id in idUser:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue

        if id > max_INT or id <= 0:
            badIds.append(id)
            continue
        if flask_login.current_user.id == id:
            return send_response(400, 3030, {"message": "Can not delete yourself"}, "error")
        
        delUser = User.query.filter_by(id = id).first()

        if delUser:
            tas = Task.query.filter_by(guarantor = id)
            objects = Maturita_Task.query.filter_by(objector = id)

            for object in objects:
                object.objector = None
            for task in tas:
                delete_teams_for_task(task.id, id)
                delete_upload_task(task.task, task.id, id)

            conversations = Conversation.query.filter(or_(Conversation.idUser1 == id, Conversation.idUser2 == id))

            for conversation in conversations:
                if conversation.idUser1 == id:
                    conversation.deletedUser1 = True
                else:
                    conversation.deletedUser2 = True

                if conversation.deletedUser1 and conversation.deletedUser2:
                    
                    if task.type == Type.Maturita:
                        if conversation.idUser1 == conversation.guarantor:
                            user = User.query.filter_by(id = conversation.idUser2).first()
                        else:
                            user = User.query.filter_by(id = conversation.idUser1).first()

                        if user.role != Role.Student:
                            continue

                        cancel_archive_conversation(conversation.idConversation, conversation.idTask, conversation.guarnator, conversation.idUser1, conversation.idUser2)

                    db.session.delete(conversation)

                db.session.commit()

            pfp_delete(delUser.profilePicture)
            db.session.delete(delUser)
            db.session.commit()
            goodIds.append(id)

    if not goodIds:
        return send_response(400, 3040, {"message": "Nothing deleted"}, "error")

    return send_response(200, 3051, {"message":"Successfuly deleted users", "deletedIds": goodIds, "notdeletedIds": badIds}, "success")

@user_bp.route("/user/update/password", methods = ["PUT"])
@flask_login.login_required
def password_reset():
    data = request.get_json(force = True)
    oldPassword = (data.get("oldPassword", None))
    newPassword = (data.get("newPassword", None))

    if not oldPassword:
        return send_response(400, 11010, {"message": "Old password not entered"}, "error")
    if not newPassword:
        return send_response(400, 11020, {"message": "New password not entered"}, "error")
    
    newPassword = str(newPassword)
    oldPassword = str(oldPassword)

    if not check_password_hash(flask_login.current_user.password, oldPassword):
        return send_response(400, 11030, {"message": "Wrong password"}, "error")
    if len(newPassword) < 5:
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
    
    email = str(email)

    if not re.match(email_regex, email):
        return send_response(400, 12020, {"message": "Wrong email format"}, "error")
    if len(email) > 255:
        return send_response(400, 12030, {"message": "Email too long"}, "error")
    if not User.query.filter_by(email = email).first():
        return send_response(400, 12040, {"message": "No user with that email addres"}, "error")
    
    token = flask_jwt_extended.create_access_token(fresh = True, identity = email, expires_delta= datetime.timedelta(hours = 1),additional_claims = {"email": email})
    link = url + "/password/forget/reset?token=" + token
    name = User.query.filter_by(email = email).first().name + " " + User.query.filter_by(email = email).first().surname
    html = email_reset_password_template(name, link)
    text = "Pro resetování hesla zkopírujte tento odkaz: " + link
    send_email(email, "Password reset", html, text)

    return send_response(201, 12051, {"message": "Token created successfuly and send to email"}, "success")

@user_bp.route("/user/password/verify", methods = ["POST"])
def password_verify():
    data = request.get_json(force = True)
    token = data.get("token", None)

    if not token:
        return send_response(400, 13010, {"message": "Token is missing"}, "error")
    
    decodedToken = flask_jwt_extended.decode_token(token)

    return send_response(200, 13021, {"message": "Verified successfuly", "email":decodedToken["email"]}, "success")

@user_bp.route("/user/password/reset", methods = ["POST"])
def password_new():
    data = request.get_json(force=True)
    email = data.get("email", None)
    newPassword = (data.get("newPassword", None))

    email = str(email)
    
    if not re.match(email_regex, email):
        return send_response(400, 14010, {"message": "Wrong email format"}, "error")
    if len(email) > 255:
        return send_response(400, 14020, {"message": "Email too long"}, "error")
    
    user = User.query.filter_by(email = email).first()

    if not user:
        return send_response(400, 14030, {"message": "Wrong email"}, "error")
    if not newPassword:
        return send_response(400, 14040, {"message": "Password missing"}, "error")
    
    newPassword = str(newPassword)

    if len(newPassword) < 5:
        return send_response(400, 14050, {"message": "Password too short"}, "error")
    
    user.password = generate_password_hash(newPassword)
    db.session.commit()
    
    return send_response(200, 14061, {"message": "Password reseted successfuly"}, "success")

@user_bp.route("/user/get/id", methods = ["GET"])
@flask_login.login_required
def get_by_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 18010, {"message": "Id not entered"}, "error")
    
    try:
        id = int(id)
    except:
        return send_response(400, 18020, {"message": "Id not integer"}, "error")
    
    if id > max_INT or id <= 0:
        return send_response(400, 18030, {"message": "Id not valid"}, "error")

    user = User.query.filter_by(id = id).first()
    
    if not user:
        return send_response(404, 18040, {"message": "User not found"}, "error")
    
    return send_response(200, 18051, {"message": "User found", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt}}, "success")

@user_bp.route("/user/get/role", methods = ["GET"])
@flask_login.login_required
def get_by_role():
    role = request.args.get("role", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    
    users = []

    if not amountForPaging:
        return send_response(400, 20010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 20020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 20030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 20040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 20050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 20060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 20070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 20080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not role:
        return send_response(400, 20090, {"message": "Role not entered"}, "error")
    
    if role not in [r.value for r in Role]:
        return send_response(400, 20100, {"message": "Role not our type"}, "error")
    
    if not searchQuery:
        user = User.query.filter_by(role = Role(role)).order_by(User.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = User.query.filter_by(role = Role(role)).order_by(User.id.desc()).count()

    else:
        user, count = user_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Role(role), typeOfSpecialSearch = "role")
            
    for u in user:
        users.append({
                        "id": u.id,
                        "name": u.name,
                        "surname": u.surname,
                        "abbreviation": u.abbreviation,
                        "role": u.role.value,
                        "profilePicture": u.profilePicture,
                        "email": u.email,
                        "idClass": all_user_classes(u.id),
                        "createdAt":u.createdAt,
                        "updatedAt":u.updatedAt
                        })
    
    return send_response(200, 20111, {"message": "Users found", "users": users, "count":count}, "success")

@user_bp.route("/user/get/number", methods = ["GET"])
@flask_login.login_required
def get_of_users():
    count = User.query.count()

    return send_response(200, 24011, {"message": "Count of users", "count": count}, "success")

@user_bp.route("/user/get/roles", methods = ["GET"])
@flask_login.login_required
def get_roles():
    roles = []
    users = User.query.order_by(User.id.desc()).all()

    for user in users:
        role = user.role.value
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
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    
    users = []

    if not amountForPaging:
        return send_response(400, 51010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 51020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 51030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 51040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 51050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 51060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 51070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 51080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not searchQuery:
        user = User.query.outerjoin(User_Class, User.id == User_Class.idUser).filter(User.role == Role.Student).filter(User_Class.idUser == None).order_by(User.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = User.query.outerjoin(User_Class, User.id == User_Class.idUser).filter(User.role == Role.Student).filter(User_Class.idUser == None).order_by(User.id.desc()).count()

    else:
        user, count = user_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, typeOfSpecialSearch = "noClass")


    for s in user:
        if not User_Class.query.filter_by(idUser = s.id).first():
            users.append({
                        "id": s.id,
                        "name": s.name,
                        "surname": s.surname,
                        "abbreviation": s.abbreviation,
                        "role": s.role.value,
                        "profilePicture": s.profilePicture,
                        "email": s.email,
                        "createdAt":s.createdAt,
                        "updatedAt":s.updatedAt
                        })

    return send_response(200, 51091, {"message": "All students without class", "users": users, "count": count}, "success")

@user_bp.route("/user/get/count/byRole", methods=["GET"])
@flask_login.login_required
def get_count_by_role():
    role = request.args.get("role", None)

    if not role:
        return send_response(400, 48010, {"message": "Role not entered"}, "error")
    
    if role not in [r.value for r in Role]:
        return send_response(400, 48020, {"message": "Role not our type"}, "error")

    count = User.query.filter_by(role=Role(role)).count()

    return send_response(200, 48031, {"message": "User count found", "count": count}, "success")

@user_bp.route("/user/logged/data", methods = ["GET"])
@flask_login.login_required
def get_logged_user_data():
    user = flask_login.current_user

    return send_response(200, 50011, {"message": "Logged user data", "user": {"id": user.id, "name": user.name, "surname": user.surname, "abbreviation": user.abbreviation, "role": user.role.value, "profilePicture": user.profilePicture, "email": user.email, "idClass": all_user_classes(user.id), "createdAt":user.createdAt, "updatedAt":user.updatedAt, "reminders":user.reminders}}, "success")

#pageNumber starts with 1
@user_bp.route("/user/get", methods = ["GET"])
@flask_login.login_required
def get_user_page():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    
    rightUsers = []

    if not amountForPaging:
        return send_response(400, 52010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 52020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 52030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 52040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 52050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 52060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 52070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 52080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not searchQuery:
        users = User.query.order_by(User.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = User.query.count()
    else:
        users, count = user_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging)

    for user in users:
        rightUsers.append({
                            "id": user.id,
                            "name": user.name,
                            "surname": user.surname,
                            "abbreviation": user.abbreviation,
                            "role": user.role.value,
                            "profilePicture": user.profilePicture,
                            "email": user.email,
                            "idClass": all_user_classes(user.id),
                            "createdAt":user.createdAt,
                            "updatedAt":user.updatedAt,
                            "reminders":user.reminders
                        })
    return send_response(200, 52091, {"message": "Users found", "users":rightUsers, "count":count}, "success")

@user_bp.route("/user/put/pfp", methods = ["PUT"])
@flask_login.login_required
def put_pfp_to_database():
    
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    profilePicture = data.get("profilePicture", None)
    
    if not idUser:
        return send_response(400, 57010, {"message": "idUser not entered"}, "error")
    if not profilePicture:
        return send_response(400, 57020, {"message": "profilePicture not entered"}, "error")
    
    try:
        idUser = int(idUser)
    except:
            return send_response(400, 57030, {"message": "IdUser not integer"}, "error")
    
    if idUser > max_INT or idUser <= 0:
        return send_response(400, 57040, {"message": "IdUser not valid"}, "error")

    user = User.query.filter_by(id = idUser).first()

    if not user:
        return send_response(400, 57050, {"message": "Wrong user id"}, "error")
    
    if flask_login.current_user.role != Role.Admin and flask_login.current_user.id != idUser:
        return send_response(403, 57060, {"message": "No permission for that"}, "error")
    
    if not pfp_check(profilePicture):
        return send_response(400, 57070, {"message": "profilePicture does not exist"}, "error")
    
    if user.profilePicture != "default.jpg":
        pfp_delete(user.profilePicture)

    user.profilePicture = profilePicture
    db.session.commit()

    return send_response(200, 57081, {"message": "profilePicture changed successfuly"}, "success")
    