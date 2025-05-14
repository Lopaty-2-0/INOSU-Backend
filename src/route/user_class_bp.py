from flask import request, Blueprint
import flask_login
from app import db
from src.models.User_Class import User_Class
from src.models.Class import Class
from src.models.User import User
from src.utils.response import sendResponse

user_class_bp = Blueprint("user_class", __name__)

@user_class_bp.route("/user_class/add", methods=["POST"])
@flask_login.login_required
def user_classAdd():
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    idClass = data.get("idClass", None)
    badIds = []
    goodIds = []

    if not idUser:
        return sendResponse(400, 26010, {"message": "idUser not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not User.query.filter_by(id = idUser).first():
        return sendResponse(400, 26010, {"message": "Nonexistent user"}, "error")
    if not Class.query.filter_by(id = idClass).first():
        return sendResponse(400, 26010, {"message": "Nonexistent class"}, "error")
    
    for id in idClass:
        if not Class.query.filter_by(id=id).first() or User_Class.query.filter_by(idUser = idUser, idClass = idClass).first():
            badIds.append(id)
        else:
            newUserClass = User_Class(idUser=idUser, idClass=id)
            db.session.add(newUserClass)
            goodIds.append(id)

    db.session.commit()
    
    return sendResponse(400, 26010, {"message": "User added to this class","badIds":badIds, "goodIds":goodIds}, "success")

@user_class_bp.route("/user_class/delete", methods=["DELETE"])
@flask_login.login_required
def user_classDelete():
    data = request.get_json(force=True)
    idUser = data.get("idUser", None)
    idClass = data.get("idClass", None)

    if not idUser:
        return sendResponse(400, 26010, {"message": "idUser not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    
    user_cl = User_Class.query.filter_by(idUser = idUser, idClass = idClass).first()

    if not user_cl:
        return sendResponse(400, 26010, {"message": "This user is not in this class"}, "error")
    
    db.session.delete(user_cl)
    db.session.commit()

    return sendResponse(400, 26010, {"message": "User deleted from this class"}, "success")

@user_class_bp.route("/user_class/get/users", methods=["GET"])
@flask_login.login_required
def user_classGetUsers():
    idClass = request.args.get("idClass", None)
    classes = User_Class.query.filter_by(idClass)
    users = []

    for cl in classes:
        users.append(cl.idUser)

    return sendResponse(400, 26010, {"message": "Users found", "users":users}, "success")