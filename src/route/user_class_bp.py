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

#TODO: idk jestli chce i tady query
@flask_login.login_required
@user_class_bp.route("/user_class/get/users", methods=["GET"])
def get_users():
    idClass = request.args.get("idClass", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    
    right_users = []

    if not amountForPaging:
        return send_response(400, 35010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 35020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 35030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 35040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 35050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 35060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idClass:
        return send_response(400, 35070, {"message":"IdClass not entered"}, "error")
    if not Class.query.filter_by(id = idClass).first():
        return send_response(400, 35080, {"message":"Nonexistent class"}, "error")
    
    users = User_Class.query.filter_by(idClass = idClass).offset(pageNumber * amountForPaging).limit(amountForPaging)
    count =  User_Class.query.filter_by(idClass = idClass).count()

    if not users:
        return send_response(400, 35090, {"message":"No users found"}, "error")
    
    for u in users:
        user = User.query.filter_by(id = u.idUser).first()
        right_users.append({
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

    return send_response(200, 35101, {"message": "Users found", "users":right_users, "count":count}, "success")