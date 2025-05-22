from flask import request, Blueprint
import flask_login
from app import db
from src.models.Task_Class import Task_Class
from src.models.Task import Task
from src.models.Class import Class
from src.models.User_Class import User_Class
from src.models.User_Task import User_Task
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
        return sendResponse(403, 26010, {"message":"Students can not make tasks"}, "error")

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    
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
        return sendResponse(400, 26010, {"message": "Nothing created"}, "error")
    
    return sendResponse(201, 26010, {"message": "Task_class created successfuly", "badIds":badIds, "goodIds":goodIds}, "success")

@task_class_bp.route("/task_class/delete", methods=["DELETE"])
@flask_login.login_required
def task_classDelete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)
    badIds = []
    goodIds = []

    if not isinstance(idClass, list):
        idClass = [idClass]
    if flask_login.current_user.role == "student":
        return sendResponse(403, 26010, {"message":"Students can not make tasks"}, "error")

    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")

    for id in idClass:
        if not Class.query.filter_by(id=id).first():
            return sendResponse(400, 26010, {"message": "Nonexistent class"}, "error")
        
        task_class = Task_Class.query.filter_by(idTask = idTask, idClass = id).first()

        if not task_class:
            badIds.append(id)
            continue

        db.session.delete(task_class)
        goodIds.append(id)

    if not goodIds:
        return sendResponse(400, 26010, {"message": "Nothing deleted"}, "error")
    
    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class deleted successfuly"}, "success")

@task_class_bp.route("/task_class/update", methods=["PUT"])
@flask_login.login_required
async def task_classUpdate():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idClass = data.get("idClass", None)
    goodIds = []
    badIds = []
    userClass = []

    if flask_login.current_user.role == "student":
        return sendResponse(403, 26010, {"message": "No permission"}, "error")
    if not idTask:
        return sendResponse(400, 26010, {"message": "idTask not entered"}, "error")
    if not idClass:
        return sendResponse(400, 26010, {"message": "idClass not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 26010, {"message": "Nonexistent task"}, "error")
    
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
        return sendResponse(400, 26010, {"message": "Nothing updated"}, "error")
    
    for user in User_Task.query.filter_by(idTask = idTask):
        for cl in User_Class.query.filter_by(idUser = user.idUser):
            userClass.append(cl.idClass)
            
        if not any(id in goodIds for id in userClass):
            await user_taskDelete(task_path, user.idUser, idTask)
            db.session.delete(user)
        userClass = []

    db.session.commit()

    return sendResponse(200, 26010, {"message": "Task_class updated", "badIds":badIds, "goodIds":goodIds}, "success")