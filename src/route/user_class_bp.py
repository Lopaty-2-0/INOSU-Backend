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

    if not idUser:
        return sendResponse(400, 26010, {"message": "idUser not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    
    user = User.query.filter_by(id = idUser).first()
    cl = Class.query.filter_by(id = idClass).first()

    if not user:
        return sendResponse(400, 26010, {"message": "Nonexistent user"}, "error")
    if not cl:
        return sendResponse(400, 26010, {"message": "Nonexistent class"}, "error")
    if User_Class.query.filter_by(idUser = idUser, idClass = idClass).first():
        return sendResponse(400, 26010, {"message": "This user is already in this class"}, "error")
    
    user_cl = User_Class(idUser=idUser, idClass=idClass)
    db.session.add(user_cl)
    db.session.commit()

    return sendResponse(400, 26010, {"message": "User added to this class", "idUser": user_cl.idUser, "idClass":user_cl.idClass}, "success")