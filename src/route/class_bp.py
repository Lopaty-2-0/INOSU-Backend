import flask_login
from src.models.Class import Class
from src.models.Specialization import Specialization
from src.utils.paging import class_paging
from src.utils.response import send_response
from src.utils.enums import Role
from flask import request, Blueprint
from app import db, max_INT
from src.utils.check_file import check_file_size
import json

#TODO: přidat export (json)

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
    
    group = str(group)
    name = str(name)
    
    try:
        grade = int(grade)
    except:
        return send_response(400, 8060, {"message": "Grade not integer"}, "error")
    if grade > max_INT or grade <= 0:
        return send_response(400, 8070, {"message": "Grade not valid"}, "error")
    if len(group) > 1:
        return send_response(400, 8080, {"message": "Group too long"}, "error")
    try:
        idSpecialization = int(idSpecialization)
    except:
        return send_response(400, 8090, {"message": "idSpecialization not integer"}, "error")
    if idSpecialization > max_INT or idSpecialization <= 0:
        return send_response(400, 8100, {"message": "idSpecialization not valid"}, "error")
    if not Specialization.query.filter_by(id = idSpecialization).first():
        return send_response(400, 8110, {"message": "Wrong idSpecialization"}, "error")
    if int(Specialization.query.filter_by(id = idSpecialization).first().lengthOfStudy) < grade:
        return send_response(400, 8120, {"message": "Grade is too much"}, "error")
    if len(name)>255:
        return send_response(400, 8130, {"message": "Name too long"}, "error")
    if Class.query.filter_by(name = name).first():
        return send_response(400, 8140, {"message": "Name already in use"}, "error")
    
    newClass = Class(grade = grade, group = group, idSpecialization = idSpecialization, name=name)
    specialization = Specialization.query.filter_by(id=idSpecialization).first()
    db.session.add(newClass)
    db.session.commit()

    return send_response (201, 8151, {"message": "Class created succesfuly", "class": {"id": newClass.id, "grade": newClass.grade, "group": newClass.group, "name":newClass.name, "specialization": specialization.abbreviation}}, "success")


@class_bp.route("/class/add/file", methods = ["POST"])
@flask_login.login_required
def add_file():
    badClasses = 0
    allClasses = 0

    classes = request.files.get("jsonFile", None)
    size = request.form.get("size", None)

    response = check_file_size(4*1024*1024, size)

    if response:
        return response
    
    file_content = classes.read().decode("utf-8").strip()

    if not file_content:
        return send_response(400, 100010, {"message": "File is empty"}, "error")

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError:
        return send_response(400, 100020, {"message": "Invalid JSON format"}, "error")
    
    for classData in data.get("classes", []):
        name = classData.get("name", None)
        grade = classData.get("grade", None)
        group = classData.get("group", None)
        idSpecialization = classData.get("idSpecialization", None)

        if not grade and not group and not idSpecialization and not name:
            badClasses += 1
            continue
        
        group = str(group)
        name = str(name)
        
        try:
            grade = int(grade)
        except:
            badClasses += 1
            continue

        if grade > max_INT or grade <= 0:
            badClasses += 1
            continue

        if len(group) > 1:
            badClasses += 1
            continue

        try:
            idSpecialization = int(idSpecialization)
        except:
            badClasses += 1
            continue

        if idSpecialization > max_INT or idSpecialization <= 0:
            badClasses += 1
            continue

        specialization = Specialization.query.filter_by(id = idSpecialization).first()

        if not specialization or int(specialization.lengthOfStudy) < grade:
            badClasses += 1
            continue

        if len(name)>255 or Class.query.filter_by(name = name).first():
            badClasses += 1
            continue

        newClass = Class(grade = grade, group = group, idSpecialization = idSpecialization, name=name)
        db.session.add(newClass)

    db.session.commit()
    
    if allClasses <= badClasses:
        return send_response (400, 100030, {"message": "No classes created"}, "error") 
            
    return send_response (201, 100041, {"message": "All classes created successfuly"}, "success")

@class_bp.route("/class/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    if flask_login.current_user.role != Role.Admin:
        return send_response(403, 9010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idClass = data.get("id", None)
    goodIds = []
    badIds = []

    if not idClass:
        return send_response(400, 9020, {"message": "Id is missing"}, "error")
    if not isinstance(idClass, list):
        idClass = [idClass]
    
    for id in idClass:
        if not Class.query.filter_by(id = id).first() or id > max_INT or id <= 0:
            badIds.append(id)
            continue

        db.session.delete(Class.query.filter_by(id = id).first())
        goodIds.append(id)

    db.session.commit()

    return send_response (200, 9031, {"message": "Class deleted successfuly", "badIds":badIds, "goodIds": goodIds}, "success")

@class_bp.route("/class/get/id", methods=["GET"])
@flask_login.login_required
def get_by_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 22010, {"message": "Id not entered"}, "error")
    try:
        id = int(id)
    except:
        return send_response(400, 22020, {"message": "Id not integer"}, "error")
    if id > max_INT or id <=0:
        return send_response(400, 22030, {"message": "Id not valid"}, "error")
        
    allClass = Class.query.filter_by(id = id).first()
    
    if not allClass:
        return send_response(404, 22040, {"message": "Class not found"}, "error")
    
    specialization = Specialization.query.filter_by(id=allClass.idSpecialization).first()

    return send_response(200, 22051, {"message": "Class found", "class": {"id": allClass.id, "grade": allClass.grade, "group": allClass.group, "name":allClass.name, "specialization": specialization.abbreviation}}, "success")

@class_bp.route("/class/get", methods=["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    if not amountForPaging:
        return send_response(400, 23010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 23020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 23030, {"message": "amountForPaging smaller than 1"}, "error")
    if amountForPaging > max_INT:
        return send_response(400, 23040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 23050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 23060, {"message": "pageNumber not integer"}, "error")
    if amountForPaging > max_INT + 1:
        return send_response(400, 23070, {"message": "amountForPaging too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 23080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        classes = Class.query.order_by(Class.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Class.query.count()
    else:
        classes, count = class_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber)

    allClass = []

    for cl in classes:
        specialization = Specialization.query.filter_by(id=cl.idSpecialization).first()
        allClass.append({
                        "id": cl.id,
                        "grade": cl.grade,
                        "group": cl.group,
                        "name": cl.name,
                        "specialization": specialization.abbreviation
                        })
        
    
    return send_response(200, 23091, {"message": "Classes found", "classes": allClass, "count":count}, "success")

@class_bp.route("/class/count", methods=["GET"])
@flask_login.login_required
def get_count():
    count = Class.query.count()

    return send_response(200, 49011, {"message": "Class count found", "count": count}, "success") 