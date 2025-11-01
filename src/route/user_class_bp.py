from flask import request, Blueprint
import flask_login
import json
from app import db
from src.models.User_Class import User_Class
from src.models.Class import Class
from src.models.User import User
from src.utils.response import send_response
from src.utils.all_user_classes import all_user_classes
from urllib.parse import unquote
from src.utils.enums import Role

user_class_bp = Blueprint("user_class", __name__)

@user_class_bp.route("/user_class/add", methods=["POST"])
@flask_login.login_required
def add():
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    idClass = data.get("idClass", None)
    badIds = []
    goodIds = []

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 33010, {"message": "Permission denied"}, "error")
    if not idUser:
        return send_response(400, 33020, {"message": "idUser not entered"}, "error")
    if not idClass:
        return send_response(400, 33030, {"message": "idClass not entered"}, "error")
    if not User.query.filter_by(id = idUser).first():
        return send_response(400, 33040, {"message": "Nonexistent user"}, "error")
    if not Class.query.filter_by(id = idClass).first():
        return send_response(400, 33050, {"message": "Nonexistent class"}, "error")
    if not isinstance(idClass, list):
        idClass = [idClass]
    
    for id in idClass:
        if not Class.query.filter_by(id=id).first() or User_Class.query.filter_by(idUser = idUser, idClass = idClass).first() or User.query.filter_by(id = idUser).first().role:
            badIds.append(id)
        else:
            newUserClass = User_Class(idUser=idUser, idClass=id)
            db.session.add(newUserClass)
            goodIds.append(id)

    if not goodIds:
        return send_response(400, 33060, {"message": "Nothing created"}, "error")

    db.session.commit()
    
    return send_response(201, 33071, {"message": "User added to this class","badIds":badIds, "goodIds":goodIds}, "success")

@user_class_bp.route("/user_class/delete", methods=["DELETE"])
@flask_login.login_required
async def delete():
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    idClass = data.get("idClass", None)

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 34010, {"message": "Permission denied"}, "error")
    if not idUser:
        return send_response(400, 34020, {"message": "idUser not entered"}, "error")
    if not idClass:
        return send_response(400, 34030, {"message": "idClass not entered"}, "error")
    
    user_cl = User_Class.query.filter_by(idUser = idUser, idClass = idClass).first()

    if not user_cl:
        return send_response(400, 34040, {"message": "This user is not in this class"}, "error")
    
    db.session.delete(user_cl)
    db.session.commit()

    return send_response(200, 34051, {"message": "User deleted from this class"}, "success")

#TODO: předělat na paging
@user_class_bp.route("/user_class/get/users", methods=["GET"])
@flask_login.login_required
def get_users():
    idClass = request.args.get("idClass", "")
    users = []
    badIds = []
    goodIds = []
    ids = []

    try:
        decoded_status = unquote(idClass)
        idClass = json.loads(decoded_status) if decoded_status.strip() else []
    except:
        idClass = []

    if not isinstance(idClass, list):
        idClass = [idClass]

    for id in idClass:
        if not Class.query.filter_by(id = id).first():
            badIds.append(id)
            continue

        clas = User_Class.query.filter_by(idClass = id)

        for cl in clas:
            if not cl.idUser in ids:
                user = User.query.filter_by(id = cl.idUser).first()
                users.append({
                            "id": user.id,
                            "name": user.name,
                            "surname": user.surname,
                            "abbreviation": user.abbreviation,
                            "role": user.role.value,
                            "profilePicture": user.profilePicture,
                            "email": user.email,
                            "idClass": all_user_classes(user.id),
                            "createdAt":user.createdAt,
                            "updatedAt":user.updatedAt
                            })
                ids.append(cl.idUser)

        goodIds.append(id)

    if not goodIds:
        return send_response(400, 35010, {"message": "Only wrong idClass"}, "error")

    return send_response(200, 35021, {"message": "Users found", "users":users, "badIds":badIds, "goodIds":goodIds}, "success")