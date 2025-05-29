from flask import request, Blueprint
import flask_login
from app import db
from src.models.User_Task import User_Task
from src.models.Task import Task
from src.models.Task_Class import Task_Class
from src.models.User_Class import User_Class
from src.models.User import User
from src.utils.response import sendResponse
from src.utils.allUserTasks import allUserTasks
from src.utils.task import taskDeleteSftp, taskSaveSftp, user_taskDelete
from src.utils.checkFileSize import checkFileSize
from src.utils.allUserClasses import allUserClasses
import json
from urllib.parse import unquote

user_task_bp = Blueprint("user_task", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]
task_path = "/home/filemanager/files/tasks/"

@user_task_bp.route("/user_task/add", methods=["POST"])
@flask_login.login_required
def user_taskAdd():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    badIds = []
    goodIds = []

    if not idTask:
        return sendResponse(400, 36010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return sendResponse(400, 36020, {"message": "idUser not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 36030, {"message": "Nonexistent task"}, "error")
    if Task.query.filter_by(id = idTask).first().approve:
        if not Task_Class.query.filter_by(idTask=idTask).first():
            status = "waiting"
        else:
            status = "pending"
    else:
        status = "approved"

    tc = Task_Class.query.filter_by(idTask=idTask)

    if not isinstance(idUser, list):
        idUser = [idUser]

    for idU in idUser:
        if User_Task.query.filter_by(idUser = idU, idTask = idTask).first() or not User.query.filter_by(id=idU).first():
            badIds.append(idU)
            continue

        cl = User_Class.query.filter_by(idUser=idU)
        status1 = False

        if tc:
            for c in cl:
                for t in tc:
                    if c.idClass == t.idClass:
                        newUser_Task = User_Task(idUser=idU, idTask=idTask, elaboration=None, review=None, status=status)
                        db.session.add(newUser_Task)
                        goodIds.append(idU)
                        status1 = True
                        break

                if status1:
                    break
        else:
            if flask_login.current_user.id == Task.query.filter_by(id = idTask).first().guarantor:
                newUser_Task = User_Task(idUser=idU, idTask=idTask, elaboration=None, review=None, status=status)
                db.session.add(newUser_Task)
                goodIds.append(idU)
                status1 = True

        if not status1:
            badIds.append(idU)

    if not goodIds:
        return sendResponse(400, 36040, {"message": "Nothing created"}, "error")

    db.session.commit()

    return sendResponse(201, 36051, {"message": "User_task created successfuly","badIds":badIds, "goodIds":goodIds}, "success")

@user_task_bp.route("/user_task/delete", methods=["DELETE"])
@flask_login.login_required
def user_taskDel():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)

    if not idTask:
        return sendResponse(400, 37010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return sendResponse(400, 37020, {"message": "idUser not entered"}, "error")
    
    user_task = User_Task.query.filter_by(idTask = idTask, idUser = idUser).first()

    if not user_task:
        return sendResponse(400, 37030, {"message": "Nonexistent user_task"}, "error")

    db.session.delete(user_task)
    db.session.commit()

    return sendResponse(200, 37041, {"message": "User_task deleted successfuly"}, "success")

@user_task_bp.route("/user_task/update", methods=["PUT"])
@checkFileSize(32 * 1024 * 1024)
@flask_login.login_required
async def user_taskUpdate():
    idTask = request.form.get("idTask", None)
    idUser = request.form.get("idUser", None)
    status = request.form.get("status", None)
    elaboration = request.files.get("elaboration", None)
    review = request.files.get("review", None)
    currentUser = flask_login.current_user

    if not idTask:
        return sendResponse(400, 38010, {"message": "idTask not entered"}, "error")
    if not idUser:
        idUser = currentUser.id
    
    task = Task.query.filter_by(id = idTask).first()
    user_task = User_Task.query.filter_by(idUser = idUser, idTask = idTask).first()

    if not User.query.filter_by(id = idUser).first():
        return sendResponse(400, 38020, {"message": "Nonexistent user"}, "error") 
    if not task:
        return sendResponse(400, 38030, {"message": "Nonexistent task"}, "error") 
    if not user_task:
        return sendResponse(400, 38040, {"message": "Nonexistent user_task"}, "error")
            
    if currentUser.id == task.guarantor:
        if not review and not status:
            return sendResponse(400, 38050, {"message": "Nothing entered to change"}, "error")
        if task.approve:
            if (user_task.status == "pending") and (str(status).lower() == "approved" or str(status).lower() == "rejected"):
                user_task.status = status.lower()
        if review:
            if not review.filename.rsplit(".", 1)[1].lower() in task_extensions:
                return sendResponse(400, 38060, {"message": "Wrong file format"}, "error")
            if not user_task.status == "approved":
                return sendResponse(400, 38070, {"message": "Can not do that"}, "error")
            if len(review.filename) > 255:
                return sendResponse(400, 38080, {"message": "File name too long"}, "error")
            if user_task.review:
                await taskDeleteSftp(task_path + str(task.id) + "/", idUser)

            filename = await taskSaveSftp(task_path + str(task.id) + "/", review, idUser)
            user_task.review = filename

    elif currentUser.id == user_task.idUser and (user_task.status == "approved" or user_task.status == "waiting"):
        if not elaboration and not status:
            return sendResponse(400, 38090, {"message": "Nothing entered to change"}, "error")
        if elaboration and user_task.status == "approved":
            if not elaboration.filename.rsplit(".", 1)[1].lower() in task_extensions:
                return sendResponse(400, 38100, {"message": "Wrong file format"}, "error")
            if len(elaboration.filename) > 255:
                return sendResponse(400, 38110, {"message": "File name too long"}, "error")
            if user_task.elaboration:
                await taskDeleteSftp(task_path + str(task.id) + "/", currentUser.id)

            filename = await taskSaveSftp(task_path + str(task.id) + "/", elaboration, currentUser.id)
            user_task.elaboration = filename

        if user_task.status == "waiting":
            if not status:
                db.session.delete(user_task)
                await user_taskDelete(task_path, currentUser.id, idTask)               
            else:
                user_task.status = "pending"
    else:
        return sendResponse(403, 38120, {"message": "Permission denied"}, "error")
    
    db.session.commit()

    return sendResponse(200, 38131, {"message": "User_Task successfuly updated"}, "success") 

@user_task_bp.route("/user_task/get", methods=["GET"])
@flask_login.login_required
def user_taskGet():
    idUser = request.args.get("idUser", None)
    classTasks = []

    if not idUser:
        return sendResponse(400, 39010, {"message": "idUser not entered"}, "error")
    if not User.query.filter_by(id = idUser).first():
        return sendResponse(400, 39020, {"message": "Nonexistent user"}, "error")
    
    task = User_Task.query.filter_by(idUser = idUser)
    classes = User_Class.query.filter_by(idUser = idUser)

    if task:
        tasks = allUserTasks(idUser)
    else:
        tasks = []

    for c in classes:
        cl = {"idClass":c.idClass, "tasks":[]}
        task_class = Task_Class.query.filter_by(idClass = c.idClass)

        for t in task_class:
            tas = Task.query.filter_by(id = t.idTask).first()
            user = User.query.filter_by(id = tas.guarantor).first()
            guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role, "profilePicture":user.profilePicture, "email":user.email, "createdAt":user.createdAt}
            cl["tasks"].append({"id":t.idTask, "name":tas.name, "startDate":tas.startDate, "endDate":tas.endDate, "task":tas.task, "guarantor":guarantor})

        classTasks.append(cl)


    return sendResponse(200, 39031, {"message": "Tasks found", "tasks":tasks, "classTasks":classTasks}, "success")

@user_task_bp.route("/user_task/get/status", methods=["GET"])
@flask_login.login_required
def user_taskGetWithStatus():
    status = request.args.get("status", "")
    which = request.args.get("which", None)
    guarantorTasks = []
    elaboratingTasks = []

    try:
        decoded_status = unquote(status)
        status = json.loads(decoded_status) if decoded_status.strip() else []
    except:
        status = []
    
    if not which:
        return sendResponse(400, 40010, {"message": "Which not entered"}, "error")

    if not isinstance(status, list):
        status = [status]
    if str(which) == "0" or str(which) == "2":
        for s in status:
            task = Task.query.filter_by(guarantor = flask_login.current_user.id)
            for tas in task:
                ta = User_Task.query.filter_by(idTask = tas.id, status = s)

                for t in ta:
                    user = User.query.filter_by(id = t.idUser).first()
                    guarantorTasks.append({"elaborator":{"id": user.id, 
                                                "name": user.name, 
                                                "surname": user.surname, 
                                                "abbreviation": user.abbreviation, 
                                                "role": user.role, 
                                                "profilePicture": user.profilePicture, 
                                                "email": user.email, 
                                                "idClass": allUserClasses(user.id),
                                                "createdAt":user.createdAt
                                                },
                                "task":tas.task,
                                "name":tas.name, 
                                "statDate":tas.startDate, 
                                "endDate":tas.endDate, 
                                "status":t.status, 
                                "elaboration":t.elaboration,
                                "review":t.review,
                                "guarantor":{"id": flask_login.current_user.id, 
                                            "name": flask_login.current_user.name, 
                                            "surname": flask_login.current_user.surname, 
                                            "abbreviation": flask_login.current_user.abbreviation, 
                                            "role": flask_login.current_user.role, 
                                            "profilePicture": flask_login.current_user.profilePicture, 
                                            "email": flask_login.current_user.email, 
                                            "idClass": allUserClasses(flask_login.current_user.id), 
                                            "createdAt":flask_login.current_user.createdAt
                                            },
                                            "idTask":tas.id
                                })
                    
    if str(which) == "1" or str(which) == "2":
        for s in status:
            ta = User_Task.query.filter_by(idUser = flask_login.current_user.id, status = s)

            for t in ta:
                tas = Task.query.filter_by(id = t.idTask).first()
                user = User.query.filter_by(id = tas.guarantor).first()
                elaboratingTasks.append({"elaborator":{"id": flask_login.current_user.id, 
                                        "name": flask_login.current_user.name, 
                                        "surname": flask_login.current_user.surname, 
                                        "abbreviation": flask_login.current_user.abbreviation, 
                                        "role": flask_login.current_user.role, 
                                        "profilePicture": flask_login.current_user.profilePicture, 
                                        "email": flask_login.current_user.email, 
                                        "idClass": allUserClasses(flask_login.current_user.id), 
                                        "createdAt":flask_login.current_user.createdAt
                                        },
                            "task":tas.task,
                            "name":tas.name, 
                            "statDate":tas.startDate, 
                            "endDate":tas.endDate, 
                            "status":t.status,
                            "elaboration":t.elaboration,
                            "review":t.review, 
                            "guarantor":{"id": user.id, 
                                            "name": user.name, 
                                            "surname": user.surname, 
                                            "abbreviation": user.abbreviation, 
                                            "role": user.role, 
                                            "profilePicture": user.profilePicture, 
                                            "email": user.email, 
                                            "idClass": allUserClasses(user.id), 
                                            "createdAt":user.createdAt
                                        },
                                        "idTask":t.idTask
                            })
                
    return sendResponse(200, 40021, {"message": "All tasks with these statuses for current user", "guarantorTasks":guarantorTasks, "elaboratingTasks":elaboratingTasks}, "success")

@user_task_bp.route("/user_task/get/idTask", methods=["GET"])
@flask_login.login_required
def user_taskGetByidTask():
    idTask = request.args.get("idTask", None)
    users = []

    if not idTask:
        return sendResponse(400, 42010, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return sendResponse(400, 42020, {"message": "Nonexistent task"}, "error")
    
    task = User_Task.query.filter_by(idTask = idTask)

    if not task:
        return sendResponse(400, 42030, {"message": "No user has this task"}, "error")

    for t in task:
        user = User.query.filter_by(id = t.idUser).first()
        users.append(user.id)

    return sendResponse(200, 42041, {"message": "Users found", "users":users}, "success")

@user_task_bp.route("/user_task/change", methods=["PUT"])
@flask_login.login_required
async def user_taskChange():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    goodIds = []
    badIds = []
    ids = []
    removedIds = []

    if not idTask:
        return sendResponse(400, 43010, {"message": "idTask not entered"}, "error")
    if not idUser:
        ids.append("all")
    if not Task.query.filter_by(id=idTask).first():
        return sendResponse(400, 43020, {"message": "Nonexistent task"}, "error")
    if Task_Class.query.filter_by(idTask = idTask).first():
        return sendResponse(400, 43030, {"message": "Task is only for classes"}, "error")
    if flask_login.current_user.id != Task.query.filter_by(id = idTask).first().guarantor:
        return sendResponse(403, 43040, {"message": "No permission"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]
    
    user_task = User_Task.query.filter_by(idTask = idTask)

    for id in idUser:
        if not User.query.filter_by(id = id).first():
            badIds.append(id)
            continue
        ids.append(id)

    for task in user_task:
        if not task.idUser in ids:
            await user_taskDelete(task_path, task.idUser, idTask)
            db.session.delete(task)
            removedIds.append(task.idUser)
            continue
        ids.remove(task.idUser)
    
    if len(ids) >= 1 and ids[0]!="all":
        if Task.query.filter_by(id = idTask).first().approve:
            status = "waiting"
        else:
            status = "approved"

        for id in ids:
            newUser_Task = User_Task(idTask=idTask,idUser=id, review=None, status=status, elaboration=None)
            goodIds.append(id)
            db.session.add(newUser_Task)

    if not goodIds and not ids and not removedIds:
        return sendResponse(400, 43050, {"message": "Nothing updated"}, "error")

    db.session.commit()

    return sendResponse(200, 43061, {"message": "User_tasks changed", "badIds":badIds, "goodIds":goodIds, "removedIds":removedIds}, "success")

@user_task_bp.route("/user_task/get/status/idTask", methods=["GET"])
@flask_login.login_required
def user_taskGetWithStatusAndIdTask():
    status = request.args.get("status", "")
    idTask = request.args.get("idTask", None)
    tasks = []

    try:
        decoded_status = unquote(status)
        status = json.loads(decoded_status) if decoded_status.strip() else []
    except:
        status = []
    
    if not idTask:
        return sendResponse(400, 44010, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return sendResponse(400, 44020, {"message": "Nonexistent task"}, "error")
    if not isinstance(status, list):
        status = [status]

    tas = Task.query.filter_by(id = idTask).first()
    guarantor = User.query.filter_by(id = tas.guarantor).first()

    if flask_login.current_user.id != tas.guarantor:
        return sendResponse(403, 44030, {"message": "No permission"}, "error")

    for s in status:
        ta = User_Task.query.filter_by(idTask = idTask, status = s)
        for t in ta:
            user = User.query.filter_by(id = t.idUser).first()
            tasks.append({"elaborator":{"id": user.id, 
                                        "name": user.name, 
                                        "surname": user.surname, 
                                        "abbreviation": user.abbreviation, 
                                        "role": user.role, 
                                        "profilePicture": user.profilePicture, 
                                        "email": user.email, 
                                        "idClass": allUserClasses(user.id),
                                        "createdAt":user.createdAt
                                        },
                        "task":tas.task,
                        "name":tas.name, 
                        "statDate":tas.startDate, 
                        "endDate":tas.endDate, 
                        "status":t.status, 
                        "elaboration":t.elaboration,
                        "review":t.review,
                        "guarantor":{"id": guarantor.id, 
                                    "name": guarantor.name, 
                                    "surname": guarantor.surname, 
                                    "abbreviation": guarantor.abbreviation, 
                                    "role": guarantor.role, 
                                    "profilePicture": guarantor.profilePicture, 
                                    "email": guarantor.email, 
                                    "idClass": allUserClasses(guarantor.id), 
                                    "createdAt":guarantor.createdAt
                                    },
                                    "idTask":tas.id
                        })
                
    return sendResponse(200, 44041, {"message": "All User_Tasks for this task and statuses", "tasks": tasks}, "success")


@user_task_bp.route("/user_task/get/idUser/idTask", methods = ["GET"])
@flask_login.login_required
def get():
    idUser = request.args.get("idUser", None)
    idTask = request.args.get("idTask", None)

    if not idTask:
        return sendResponse(400, 45010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return sendResponse(400, 45020, {"message": "idUser not entered"}, "error")
    
    user_task = User_Task.query.filter_by(idUser = idUser, idTask = idTask).first()
    user = User.query.filter_by(id = idUser).first()
    task = Task.query.filter_by(id = idTask).first()
    
    if not user:
        return sendResponse(400, 45030, {"message": "Nonexistent user"}, "error")
    if not task:
        return sendResponse(400, 45040, {"message": "Nonexistent task"}, "error")
    if not user_task:
        return sendResponse(400, 45050, {"message": "Nonexistent user_task"}, "error")
    
    guarantor = User.query.filter_by(id = task.guarantor).first()

    tasks = {"elaborator":{"id": user.id, 
                                "name": user.name, 
                                "surname": user.surname, 
                                "abbreviation": user.abbreviation, 
                                "role": user.role, 
                                "profilePicture": user.profilePicture, 
                                "email": user.email, 
                                "idClass": allUserClasses(user.id),
                                "createdAt":user.createdAt
                                },
                "task":task.task,
                "name":task.name, 
                "statDate":task.startDate, 
                "endDate":task.endDate, 
                "status":user_task.status, 
                "elaboration":user_task.elaboration,
                "review":user_task.review,
                "guarantor":{"id": guarantor.id, 
                            "name": guarantor.name, 
                            "surname": guarantor.surname, 
                            "abbreviation": guarantor.abbreviation, 
                            "role": guarantor.role, 
                            "profilePicture": guarantor.profilePicture, 
                            "email": guarantor.email, 
                            "idClass": allUserClasses(guarantor.id), 
                            "createdAt":guarantor.createdAt
                            },
                            "idTask":task.id
                }
    
    return sendResponse(200, 45061, {"message": "All User_Tasks for this task and statuses", "task": tasks}, "success")