from flask import request, Blueprint
import flask_login
import json
from app import db, task_path
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.models.User_Class import User_Class
from src.models.User import User
from src.utils.response import send_response
from src.utils.all_user_tasks import all_user_tasks
from src.utils.task import task_delete_sftp, task_save_sftp, user_task_delete, user_task_createDir
from src.utils.check_file import check_file_size
from src.utils.all_user_classes import all_user_classes
from urllib.parse import unquote

user_team_bp = Blueprint("user_team", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@user_team_bp.route("/user_team/add", methods=["POST"])
@flask_login.login_required
async def add():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    idClass = data.get("idClass", None)
    badIds = []
    goodIds = []

    if not idTask:
        return send_response(400, 36010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 36020, {"message": "idUser not entered"}, "error")
    if not Task.query.filter_by(id=idTask).first():
        return send_response(400, 36030, {"message": "Nonexistent task"}, "error")
    if not idClass:
        if Task.query.filter_by(id = idTask).first().approve:
            if not Task_Class.query.filter_by(idTask=idTask).first():
                status = "waiting"
            else:
                status = "pending"
    else:
        status = "approved"


    if not isinstance(idUser, list):
        idUser = [idUser]

    for idU in idUser:
        if User_Team.query.filter_by(idUser = idU, idTask = idTask).first() or not User.query.filter_by(id=idU).first():
            badIds.append(idU)
            continue

        cl = User_Class.query.filter_by(idUser=idU)
        status1 = False

        if tc:
            for c in cl:
                for t in tc:
                    if c.idClass == t.idClass:
                        newuUser_Team = User_Team(idUser=idU, idTask=idTask, elaboration=None, review=None, status=status)
                        await user_task_createDir(task_path + str(idTask) + "/", idU)
                        db.session.add(newUser_Team)
                        goodIds.append(idU)
                        status1 = True
                        break

                if status1:
                    break
        else:
            if flask_login.current_user.id == Task.query.filter_by(id = idTask).first().guarantor:
                newUser_Team = User_Team(idUser=idU, idTask=idTask, elaboration=None, review=None, status=status)
                await user_task_createDir(task_path + str(idTask) + "/", idU)
                db.session.add(newUser_Team)
                goodIds.append(idU)
                status1 = True

        if not status1:
            badIds.append(idU)

    if not goodIds:
        return send_response(400, 36040, {"message": "Nothing created"}, "error")

    db.session.commit()

    return send_response(201, 36051, {"message": "user_team created successfuly","badIds":badIds, "goodIds":goodIds}, "success")

@user_team_bp.route("/user_team/delete", methods=["DELETE"])
@flask_login.login_required
def delete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)

    if not idTask:
        return send_response(400, 37010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 37020, {"message": "idUser not entered"}, "error")
    
    user_team = User_Team.query.filter_by(idTask = idTask, idUser = idUser).first()

    if not user_team:
        return send_response(400, 37030, {"message": "Nonexistent user_team"}, "error")

    db.session.delete(user_team)
    db.session.commit()

    return send_response(200, 37041, {"message": "user_team deleted successfuly"}, "success")

@user_team_bp.route("/user_team/update", methods=["PUT"])
@check_file_size(32 * 1024 * 1024)
@flask_login.login_required
async def update():
    idTask = request.form.get("idTask", None)
    idUser = request.form.get("idUser", None)
    status = request.form.get("status", None)
    elaboration = request.files.get("elaboration", None)
    review = request.files.get("review", None)
    currentUser = flask_login.current_user

    if not idTask:
        return send_response(400, 38010, {"message": "idTask not entered"}, "error")
    if not idUser:
        idUser = currentUser.id
    
    task = Task.query.filter_by(id = idTask).first()
    user_team = User_Team.query.filter_by(idUser = idUser, idTask = idTask).first()

    if not User.query.filter_by(id = idUser).first():
        return send_response(400, 38020, {"message": "Nonexistent user"}, "error") 
    if not task:
        return send_response(400, 38030, {"message": "Nonexistent task"}, "error") 
    if not user_team:
        return send_response(400, 38040, {"message": "Nonexistent user_team"}, "error")
            
    if currentUser.id == task.guarantor:
        if task.approve:
            if (user_team.status == "pending") and (str(status).lower() == "approved" or str(status).lower() == "rejected"):
                user_team.status = status.lower()
        if review:
            if not review.filename.rsplit(".", 1)[1].lower() in task_extensions:
                return send_response(400, 38050, {"message": "Wrong file format"}, "error")
            if not user_team.status == "approved":
                return send_response(400, 38060, {"message": "Can not do that"}, "error")
            if len(review.filename) > 255:
                return send_response(400, 38070, {"message": "File name too long"}, "error")
            if user_team.review:
                await task_delete_sftp(task_path + str(task.id) + "/", str(idUser) + "/review")

            filename = await task_save_sftp(task_path + str(task.id) + "/", review, str(idUser) + "/review")
            user_team.review = filename
        else:
            if user_team.review:
                await task_delete_sftp(task_path + str(task.id) + "/", str(idUser) + "/review")
            user_team.review = None

    elif currentUser.id == user_team.idUser and (user_team.status == "approved" or user_team.status == "waiting"):
        if elaboration and user_team.status == "approved":
            if not elaboration.filename.rsplit(".", 1)[1].lower() in task_extensions:
                return send_response(400, 38080, {"message": "Wrong file format"}, "error")
            if len(elaboration.filename) > 255:
                return send_response(400, 38090, {"message": "File name too long"}, "error")
            if user_team.elaboration:
                await task_delete_sftp(task_path + str(task.id) + "/", str(currentUser.id) + "/elaboration")

            filename = await task_save_sftp(task_path + str(task.id) + "/", elaboration, str(currentUser.id) + "/elaboration")
            user_team.elaboration = filename

        elif user_team.status == "approved":
            if user_team.elaboration:
                await task_delete_sftp(task_path + str(task.id) + "/", str(currentUser.id) + "/elaboration")
            user_team.elaboration = None

        if user_team.status == "waiting":
            if not status:
                db.session.delete(user_team)
                await user_task_delete(task_path, str(currentUser.id) + "/elaboration", idTask)               
            else:
                user_team.status = "pending"
    else:
        return send_response(403, 38100, {"message": "Permission denied"}, "error")
    
    db.session.commit()

    return send_response(200, 38111, {"message": "User_Team successfuly updated"}, "success") 

@user_team_bp.route("/user_team/get", methods=["GET"])
@flask_login.login_required
def get():
    idUser = request.args.get("idUser", None)

    if not idUser:
        return send_response(400, 39010, {"message": "idUser not entered"}, "error")
    if not User.query.filter_by(id = idUser).first():
        return send_response(400, 39020, {"message": "Nonexistent user"}, "error")
    
    task = User_Team.query.filter_by(idUser = idUser)

    if task:
        tasks = all_user_tasks(idUser)
    else:
        tasks = []

    return send_response(200, 39031, {"message": "Tasks found", "tasks":tasks}, "success")

@user_team_bp.route("/user_team/get/status", methods=["GET"])
@flask_login.login_required
def get_by_status():
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
        return send_response(400, 40010, {"message": "Which not entered"}, "error")

    if not isinstance(status, list):
        status = [status]
    if str(which) == "0" or str(which) == "2":
        for s in status:
            task = Task.query.filter_by(guarantor = flask_login.current_user.id)
            for tas in task:
                ta = User_Team.query.filter_by(idTask = tas.id, status = s)

                for t in ta:
                    user = User.query.filter_by(id = t.idUser).first()
                    guarantorTasks.append({"elaborator":{"id": user.id, 
                                                "name": user.name, 
                                                "surname": user.surname, 
                                                "abbreviation": user.abbreviation, 
                                                "role": user.role, 
                                                "profilePicture": user.profilePicture, 
                                                "email": user.email, 
                                                "idClass": all_user_classes(user.id),
                                                "createdAt":user.createdAt,
                                                "updatedAt":user.updatedAt
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
                                            "idClass": all_user_classes(flask_login.current_user.id), 
                                            "createdAt":flask_login.current_user.createdAt,
                                            "updatedAt":flask_login.current_user.updatedAt
                                            },
                                            "idTask":tas.id
                                })
                    
    if str(which) == "1" or str(which) == "2":
        for s in status:
            ta = User_Team.query.filter_by(idUser = flask_login.current_user.id, status = s)

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
                                        "idClass": all_user_classes(flask_login.current_user.id), 
                                        "createdAt":flask_login.current_user.createdAt,
                                        "updatedAt":flask_login.current_user.updatedAt
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
                                            "idClass": all_user_classes(user.id), 
                                            "createdAt":user.createdAt,
                                            "updatedAt":user.updatedAt
                                        },
                                        "idTask":t.idTask
                            })
                
    return send_response(200, 40021, {"message": "All tasks with these statuses for current user", "guarantorTasks":guarantorTasks, "elaboratingTasks":elaboratingTasks}, "success")

@user_team_bp.route("/user_team/get/idTask", methods=["GET"])
@flask_login.login_required
def get_by_idTask():
    idTask = request.args.get("idTask", None)
    users = []

    if not idTask:
        return send_response(400, 42010, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 42020, {"message": "Nonexistent task"}, "error")
    
    task = User_Team.query.filter_by(idTask = idTask)

    if not task:
        return send_response(400, 42030, {"message": "No user has this task"}, "error")

    for t in task:
        user = User.query.filter_by(id = t.idUser).first()
        users.append(user.id)

    return send_response(200, 42041, {"message": "Users found", "users":users}, "success")

@user_team_bp.route("/user_team/change", methods=["PUT"])
@flask_login.login_required
async def change():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idUser = data.get("idUser", None)
    goodIds = []
    badIds = []
    ids = []
    removedIds = []

    if not idTask:
        return send_response(400, 43010, {"message": "idTask not entered"}, "error")
    if not idUser:
        ids.append("all")
    if not Task.query.filter_by(id=idTask).first():
        return send_response(400, 43020, {"message": "Nonexistent task"}, "error")
    if flask_login.current_user.id != Task.query.filter_by(id = idTask).first().guarantor:
        return send_response(403, 43030, {"message": "No permission"}, "error")
    if not isinstance(idUser, list):
        idUser = [idUser]
    
    user_team = User_Team.query.filter_by(idTask = idTask)

    for id in idUser:
        if not User.query.filter_by(id = id).first():
            badIds.append(id)
            continue
        ids.append(id)

    for task in user_team:
        if not task.idUser in ids:
            await user_task_delete(task_path, task.idUser, idTask)
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
            newuser_team = user_team(idTask=idTask,idUser=id, review=None, status=status, elaboration=None)
            await user_task_createDir(task_path + str(idTask) + "/", id)
            goodIds.append(id)
            db.session.add(newuser_team)

    if not goodIds and not ids and not removedIds:
        return send_response(400, 43040, {"message": "Nothing updated"}, "error")

    db.session.commit()

    return send_response(200, 43051, {"message": "user_teams changed", "badIds":badIds, "goodIds":goodIds, "removedIds":removedIds}, "success")

@user_team_bp.route("/user_team/get/status/idTask", methods=["GET"])
@flask_login.login_required
def get_with_status_and_idTask():
    status = request.args.get("status", "")
    idTask = request.args.get("idTask", None)
    tasks = []

    try:
        decoded_status = unquote(status)
        status = json.loads(decoded_status) if decoded_status.strip() else []
    except:
        status = []
    
    if not idTask:
        return send_response(400, 44010, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 44020, {"message": "Nonexistent task"}, "error")
    if not isinstance(status, list):
        status = [status]

    tas = Task.query.filter_by(id = idTask).first()
    guarantor = User.query.filter_by(id = tas.guarantor).first()

    if flask_login.current_user.id != tas.guarantor:
        return send_response(403, 44030, {"message": "No permission"}, "error")

    for s in status:
        ta = User_Team.query.filter_by(idTask = idTask, status = s)
        for t in ta:
            user = User.query.filter_by(id = t.idUser).first()
            tasks.append({"elaborator":{"id": user.id, 
                                        "name": user.name, 
                                        "surname": user.surname, 
                                        "abbreviation": user.abbreviation, 
                                        "role": user.role, 
                                        "profilePicture": user.profilePicture, 
                                        "email": user.email, 
                                        "idClass": all_user_classes(user.id),
                                        "createdAt":user.createdAt,
                                        "updatedAt":user.updatedAt
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
                                    "idClass": all_user_classes(guarantor.id), 
                                    "createdAt":guarantor.createdAt,
                                    "updatedAt":guarantor.updatedAt
                                    },
                                    "idTask":tas.id
                        })
                
    return send_response(200, 44041, {"message": "All user_teams for this task and statuses", "tasks": tasks}, "success")


@user_team_bp.route("/user_team/get/idUser/idTask", methods = ["GET"])
@flask_login.login_required
def get_by_idUser_and_idTask():
    idUser = request.args.get("idUser", None)
    idTask = request.args.get("idTask", None)

    if not idTask:
        return send_response(400, 45010, {"message": "idTask not entered"}, "error")
    if not idUser:
        return send_response(400, 45020, {"message": "idUser not entered"}, "error")
    
    user_team = User_Team.query.filter_by(idUser = idUser, idTask = idTask).first()
    user = User.query.filter_by(id = idUser).first()
    task = Task.query.filter_by(id = idTask).first()
    
    if not user:
        return send_response(400, 45030, {"message": "Nonexistent user"}, "error")
    if not task:
        return send_response(400, 45040, {"message": "Nonexistent task"}, "error")
    if not user_team:
        return send_response(400, 45050, {"message": "Nonexistent user_team"}, "error")
    
    guarantor = User.query.filter_by(id = task.guarantor).first()

    tasks = {"elaborator":{"id": user.id, 
                                "name": user.name, 
                                "surname": user.surname, 
                                "abbreviation": user.abbreviation, 
                                "role": user.role, 
                                "profilePicture": user.profilePicture, 
                                "email": user.email, 
                                "idClass": all_user_classes(user.id),
                                "createdAt":user.createdAt,
                                "updatedAt":user.updatedAt
                                },
                "task":task.task,
                "name":task.name, 
                "statDate":task.startDate, 
                "endDate":task.endDate, 
                "status":user_team.status, 
                "elaboration":user_team.elaboration,
                "review":user_team.review,
                "guarantor":{"id": guarantor.id, 
                            "name": guarantor.name, 
                            "surname": guarantor.surname, 
                            "abbreviation": guarantor.abbreviation, 
                            "role": guarantor.role, 
                            "profilePicture": guarantor.profilePicture, 
                            "email": guarantor.email, 
                            "idClass": all_user_classes(guarantor.id), 
                            "createdAt":guarantor.createdAt,
                            "updatedAt":guarantor.updatedAt
                            },
                            "idTask":task.id
                }
    
    return send_response(200, 45061, {"message": "All user_teams for this task and statuses", "task": tasks}, "success")

@user_team_bp.route("/user_team/count/approved_without_review", methods=["GET"])
@flask_login.login_required
def count_approved_without_review():
    count = User_Team.query.filter_by(status="approved", idUser = flask_login.current_user.id).filter(User_Team.review == None).count()

    return send_response(200, 47011, {"message": "Count of approved user_teams without review", "count": count}, "success")