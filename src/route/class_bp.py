import flask_login
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.Task_Class import Task_Class
from src.models.Specialization import Specialization
from src.utils.response import sendResponse
from flask import request, Blueprint
from app import db

class_bp = Blueprint("class", __name__)

@class_bp.route("/class/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != "admin":
        return sendResponse(403, 8010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    group = data.get("group", None)
    idSpecialization = data.get("idSpecialization", None)
    name = data.get("name", None)

    if not grade:
        return sendResponse(400, 8020, {"message": "Grade missing"}, "error")
    if not group:
        return sendResponse(400, 8030, {"message": "Group missing"}, "error")
    if not idSpecialization:
        return sendResponse(400, 8040, {"message": "idSpecialization missing"}, "error")
    if not name:
        return sendResponse(400, 8050, {"message": "Name missing"}, "error")
    try:
        grade = int(grade)
    except:
        return sendResponse(400, 8060, {"message": "Grade not integer"}, "error")
    if len(group) > 1:
        return sendResponse(400, 8070, {"message": "Group too long"}, "error")
    if not Specialization.query.filter_by(id = idSpecialization).first():
        return sendResponse(400, 8080, {"message": "Wrong idSpecialization"}, "error")
    if int(Specialization.query.filter_by(id = idSpecialization).first().lengthOfStudy) < grade:
        return sendResponse(400, 8090, {"message": "Grade is too much"}, "error")
    if Class.query.filter_by(name = name).first():
        return sendResponse(400, 8100, {"message": "Name already in use"}, "error")
    
    newClass = Class(grade = grade, group = group, idSpecialization = idSpecialization, name=name)
    specialization = Specialization.query.filter_by(id=idSpecialization).first()
    db.session.add(newClass)
    db.session.commit()

    return sendResponse (201, 8111, {"message": "Class created succesfuly", "class": {"id": newClass.id, "grade": newClass.grade, "group": newClass.group, "name":newClass.name, "specialization": specialization.abbrevation}}, "success")

@class_bp.route("/class/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    if flask_login.current_user.role != "admin":
        return sendResponse(403, 9010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idClass = data.get("idClass", None)

    if not idClass:
        return sendResponse(400, 9020, {"message": "IdClass is missing"}, "error")
    if not Class.query.filter_by(id = idClass).first():
        return sendResponse(400, 9030, {"message": "Wrong idClass"}, "error")
    if User_Class.query.filter_by(idClass = idClass).first():
        return sendResponse(400, 9040, {"message": "Some user still uses this class"}, "error")
    if Task_Class.query.filter_by(idClass = idClass).first():
        return sendResponse(400, 9050, {"message": "Some task still uses this class"}, "error")
    
    db.session.delete(Class.query.filter_by(id = idClass).first())
    db.session.commit()

    return sendResponse (200, 9061, {"message": "Class deleted successfuly"}, "success")

@class_bp.route("/class/get/id", methods=["GET"])
@flask_login.login_required
def getClassById():
    data = request.args.get(force=True)
    id = data.get("id", None)

    if not id:
        return sendResponse(400, 22010, {"message": "Id not entered"}, "error")

    all_class = Class.query.filter_by(id = id).first()
    
    if not all_class:
        return sendResponse(400, 22020, {"message": "Class not found"}, "error")
    
    specialization = Specialization.query.filter_by(id=all_class.idSpecialization).first()
    
    return sendResponse(200, 22031, {"message": "Class found", "class": {"id": all_class.id, "grade": all_class.grade, "group": all_class.group, "name":all_class.name, "specialization": specialization.abbrevation}}, "success")

@class_bp.route("/class/get", methods=["GET"])
@flask_login.login_required
def getClasses():
    classes = Class.query.filter_by()
    all_class = []

    for cl in classes:
        specialization = Specialization.query.filter_by(id=cl.idSpecialization).first()
        all_class.append({"id": cl.id, "grade": cl.grade, "group": cl.group,"name": cl.name,"specialization": specialization.abbrevation})
    if not all_class:
        return sendResponse(400, 23010, {"message": "Classes not found"}, "error")
    
    return sendResponse(200, 23021, {"message": "Classes found", "classes": all_class}, "success")