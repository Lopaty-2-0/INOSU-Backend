import flask_login
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.Specialization import Specialization
from src.utils.response import send_response
from src.utils.enums import Role
from flask import request, Blueprint
from app import db

class_bp = Blueprint("class", __name__)

@class_bp.route("/class/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 8010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    group = data.get("group", None)
    idSpecialization = data.get("idSpecialization", None)
    name = data.get("name", None)

    if not grade:
        return send_response(400, 8020, {"message": "Grade missing"}, "error")
    if not group:
        return send_response(400, 8030, {"message": "Group missing"}, "error")
    if not idSpecialization:
        return send_response(400, 8040, {"message": "idSpecialization missing"}, "error")
    if not name:
        return send_response(400, 8050, {"message": "Name missing"}, "error")
    try:
        grade = int(grade)
    except:
        return send_response(400, 8060, {"message": "Grade not integer"}, "error")
    if len(group) > 1:
        return send_response(400, 8070, {"message": "Group too long"}, "error")
    if not Specialization.query.filter_by(id = idSpecialization).first():
        return send_response(400, 8080, {"message": "Wrong idSpecialization"}, "error")
    if int(Specialization.query.filter_by(id = idSpecialization).first().lengthOfStudy) < grade:
        return send_response(400, 8090, {"message": "Grade is too much"}, "error")
    if Class.query.filter_by(name = name).first():
        return send_response(400, 8100, {"message": "Name already in use"}, "error")
    
    newClass = Class(grade = grade, group = group, idSpecialization = idSpecialization, name=name)
    specialization = Specialization.query.filter_by(id=idSpecialization).first()
    db.session.add(newClass)
    db.session.commit()

    return send_response (201, 8111, {"message": "Class created succesfuly", "class": {"id": newClass.id, "grade": newClass.grade, "group": newClass.group, "name":newClass.name, "specialization": specialization.abbreviation}}, "success")

@class_bp.route("/class/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 9010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idClass = data.get("idClass", None)
    goodIds = []
    badIds = []

    if not idClass:
        return send_response(400, 9020, {"message": "IdClass is missing"}, "error")
    if not isinstance(idClass, list):
        idClass = [idClass]
    
    for id in idClass:
        if not Class.query.filter_by(id = id).first():
            badIds.append(id)
            continue

        users = User_Class.query.filter_by(idClass = id)

        for user in users:
            db.session.delete(user)

        db.session.delete(Class.query.filter_by(id = id).first())
        goodIds.append(id)

    db.session.commit()

    return send_response (200, 9031, {"message": "Class deleted successfuly", "badIds":badIds, "goodIds": goodIds}, "success")

#TODO: předělat na paging
@class_bp.route("/class/get/id", methods=["GET"])
@flask_login.login_required
def get_by_id():
    data = request.args.get(force=True)
    id = data.get("id", None)

    if not id:
        return send_response(400, 22010, {"message": "Id not entered"}, "error")

    all_class = Class.query.filter_by(id = id).first()
    
    if not all_class:
        return send_response(400, 22020, {"message": "Class not found"}, "error")
    
    specialization = Specialization.query.filter_by(id=all_class.idSpecialization).first()
    
    return send_response(200, 22031, {"message": "Class found", "class": {"id": all_class.id, "grade": all_class.grade, "group": all_class.group, "name":all_class.name, "specialization": specialization.abbreviation}}, "success")

#TODO: předělat na paging
@class_bp.route("/class/get", methods=["GET"])
@flask_login.login_required
def get():
    classes = Class.query.all()
    all_class = []

    for cl in classes:
        specialization = Specialization.query.filter_by(id=cl.idSpecialization).first()
        all_class.append({"id": cl.id, "grade": cl.grade, "group": cl.group,"name": cl.name,"specialization": specialization.abbreviation})
    if not all_class:
        return send_response(400, 23010, {"message": "Classes not found"}, "error")
    
    return send_response(200, 23021, {"message": "Classes found", "classes": all_class}, "success")

@class_bp.route("/class/count", methods=["GET"])
@flask_login.login_required
def get_count():
    count = Class.query.count()

    return send_response(200, 49011, {"message": "Class count found", "count": count}, "success") 