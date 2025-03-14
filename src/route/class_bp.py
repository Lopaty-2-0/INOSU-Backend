import flask_login
from src.models.Class import Class
from src.models.User import User
from src.models.Specialization import Specialization
from src.utils.response import sendResponse
from flask import request, Blueprint
from app import db

class_bp = Blueprint("class", __name__)

@class_bp.route("/class/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != "admin":
        return sendResponse(400, 8010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    group = data.get("group", None)
    idSpecialization = data.get("idSpecialization")

    if not grade:
        return sendResponse(400, 8020, {"message": "Grade missing"}, "error")
    try:
        grade = int(grade)
    except:
        return sendResponse(400, 8030, {"message": "Grade not integer"}, "error")
    if not group:
        return sendResponse(400, 8040, {"message": "Group missing"}, "error")
    if len(group) > 1:
        return sendResponse(400, 8050, {"message": "Group too long"}, "error")
    if not idSpecialization:
        return sendResponse(400, 8060, {"message": "idSpecialization missing"}, "error")
    if not Specialization.query.filter_by(id = idSpecialization).first():
        return sendResponse(400, 8070, {"message": "Wrong idSpecialization"}, "error")
    if int(Specialization.query.filter_by(id = idSpecialization).first().lengthOfStudy) < grade:
        return sendResponse(400, 8080, {"message": "Grade is too much"}, "error")
    
    newClass = Class(grade = grade, group = group, idSpecialization = idSpecialization)
    db.session.add(newClass)
    db.session.commit()

    return sendResponse (201, 8091, {"message": "Class created succesfuly"}, "succes")

@class_bp.route("/class/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    if flask_login.current_user.role != "admin":
        return sendResponse(400, 9010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idClass = data.get("idClass", None)

    if not idClass:
        return sendResponse(400, 9020, {"message": "IdClass is missing"}, "error")
    if not Class.query.filter_by(id = idClass).first():
        return sendResponse(400, 9030, {"message": "Wrong idClass"}, "error")
    if User.query.filter_by(idClass = idClass).first():
        return sendResponse(400, 9040, {"message": "Some student still uses this specialization"}, "error")
    
    db.session.delete(Class.query.filter_by(id = idClass).first())
    db.session.commit()

    return sendResponse (201, 9051, {"message": "Class deleted succesfuly"}, "succes")