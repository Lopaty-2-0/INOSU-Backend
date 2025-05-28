from flask import request, Blueprint
import flask_login
from app import db
from src.models.Task_Class import Task_Class
from src.models.Task import Task
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.User_Task import User_Task
from src.models.Specialization import Specialization
from src.utils.task import user_taskDelete
from src.utils.response import sendResponse

task_class_bp = Blueprint("task_class", __name__)
task_path = "/home/filemanager/files/tasks/"

@task_class_bp.route("/task_class/add", methods=["POST"])
@flask_login.login_required
def task_classAdd():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)
    badIds = []
    goodIds = []

    if flask_login.current_user.role == "student":
        return sendResponse(403, 30010, {"message":"Students can not make tasks"}, "error")

    if not idTask:
        return sendResponse(400, 30020, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 30030, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 30040, {"message": "Nonexistent task"}, "error")
    if not isinstance(idClass, list):
        idClass = [idClass]
    
    for id in idClass:
        if not Class.query.filter_by(id=id).first():
            badIds.append(id)
        elif Task_Class.query.filter_by(idTask = idTask, idClass = id).first():
            badIds.append(id)
        else:
            newTaskClass = Task_Class(idTask=idTask, idClass=id)
            db.session.add(newTaskClass)
            goodIds.append(id)

    db.session.commit()

    if not goodIds:
        return sendResponse(400, 30050, {"message": "Nothing created"}, "error")
    
    return sendResponse(201, 30061, {"message": "Task_class created successfuly", "badIds":badIds, "goodIds":goodIds}, "success")

@task_class_bp.route("/task_class/delete", methods=["DELETE"])
@flask_login.login_required
async def task_classDelete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)
    badIds = []
    goodIds = []

    if not isinstance(idClass, list):
        idClass = [idClass]
    if flask_login.current_user.role == "student":
        return sendResponse(403, 31010, {"message":"Students can not delete tasks"}, "error")

    if not idTask:
        return sendResponse(400, 31020, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 31030, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 31040, {"message": "Nonexistent task"}, "error")

    for id in idClass:
        if not Class.query.filter_by(id=id).first():
            return sendResponse(400, 31050, {"message": "Nonexistent class"}, "error")
        
        task_class = Task_Class.query.filter_by(idTask = idTask, idClass = id).first()

        if not task_class:
            badIds.append(id)
            continue

        db.session.delete(task_class)
        goodIds.append(id)
    
    if not goodIds:
        return sendResponse(400, 31060, {"message": "Nothing deleted"}, "error")
    
    db.session.commit()

    return sendResponse(200, 31071, {"message": "Task_class deleted successfuly"}, "success")

@task_class_bp.route("/task_class/update", methods=["PUT"])
@flask_login.login_required
async def task_classUpdate():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)
    goodIds = []
    badIds = []

    if flask_login.current_user.role == "student":
        return sendResponse(403, 32010, {"message": "No permission"}, "error")
    if not idTask:
        return sendResponse(400, 32020, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 32030, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 32040, {"message": "Nonexistent task"}, "error")
    
    task_class = Task_Class.query.filter_by(idTask = idTask)

    for task in task_class:
        db.session.delete(task)

    
    for id in idClass:
        if not Class.query.filter_by(id=id).first():
            badIds.append(id)
            continue

        newMichal = Task_Class(idTask=idTask, idClass=id)
        db.session.add(newMichal)
        goodIds.append(id)

    if not goodIds:
        return sendResponse(400, 32050, {"message": "Nothing updated"}, "error")

    db.session.commit()

    return sendResponse(200, 32061, {"message": "Task_class updated", "badIds":badIds, "goodIds":goodIds}, "success")

@task_class_bp.route("/task_class/get", methods=["GET"])
@flask_login.login_required
def getByTask():
    idTask = request.args.get("idTask", None)
    classes = []

    if not idTask:
        return sendResponse(400, 41010, {"message": "idTask not entered"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()
    tasks = Task_Class.query.filter_by(idTask = idTask)

    if not task:
        return sendResponse(400, 41020, {"message": "Nonexistent task"}, "error")
    
    for t in tasks:
        cl = Class.query.filter_by(id = t.idClass).first()
        specialization = Specialization.query.filter_by(id = cl.idSpecialization).first()
        classes.append({"id": cl.id, "grade": cl.grade, "group": cl.group,"name": cl.name,"specialization": specialization.abbreviation})
    
    return sendResponse(200, 41031, {"message": "All classes for this task", "classes":classes}, "success")
        