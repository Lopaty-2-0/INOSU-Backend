from flask import request, Blueprint
import flask_login
from src.utils.response import send_response
from src.utils.check_file import check_file_size
from src.utils.task import make_task, task_delete_sftp, update_task
from src.models.User import User
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.Team import Team
from src.models.Version_Team import Version_Team
from src.models.Maturita_Task import Maturita_Task
from src.models.Maturita import Maturita
from src.models.Evaluator import Evaluator
from src.models.Topic import Topic
from src.utils.enums import Status, Type, Role
from src.utils.maturita_task import maturita_task_delete
import datetime
from src.utils.paging import task_paging
from src.utils.team import make_team
from app import db, maxINT, maxFLOAT
from src.utils.reminder import cancel_reminder

#TODO: nutné dodat u všech get, kde se získává maturita, získání topic, maturita a maturita_task
#TODO: při vytváření maturit je nutné dělat i maturita_task (kontrolovat s topic, maturita a Evaluator) + při vytváření od garanta udělat funkci na smazání všechn návrhů studenta

task_bp = Blueprint("task", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/add", methods = ["POST"])
async def add():
    taskName = request.form.get("name", None)
    endDate = request.form.get("endDate", None)
    task = request.files.get("task", None)
    deadline = request.form.get("deadline", None)
    points = request.form.get("points", None)

    startDate = datetime.datetime.now(datetime.timezone.utc)

    if flask_login.current_user.role == Role.Student:
       return send_response(403, 26010, {"message": "This role can not make tasks"}, "error")
    if not taskName:
        return send_response(400, 26020, {"message": "Name not entered"}, "error")
    if not endDate:
        return send_response(400, 26030, {"message": "endDate  not entered"}, "error")
    
    taskName = str(taskName)

    if len(taskName) > 45:
        return send_response(400, 26040, {"message":"Name too long"}, "error")
    try:
        endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 26050, {"message":"End date not integer or is too far"}, "error")
    if endDate <= startDate:
        return send_response(400, 26060, {"message":"Ending before begining"}, "error")
    if not task:
        return send_response(400, 26070, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
        return send_response(400, 26080, {"message": "Wrong file format or too long"}, "error")

    type = Type.Task
    user = flask_login.current_user

    if deadline:
        try:
            deadline = datetime.datetime.fromtimestamp(int(deadline)/1000, tz=datetime.timezone.utc)

            if deadline < startDate:
                return send_response(400, 26090, {"message":"Deadline before startDate"}, "error")
            if deadline < endDate:
                return send_response(400, 26100, {"message":"Deadline before endDate"}, "error")
        except:
            return send_response(400, 26110, {"message":"Deadline not integer or is too far"}, "error")
    else:
        deadline = None
    if points:
        try:
            points = float(points)
        except:
            return send_response(400, 26120, {"message":"Points are not float"}, "error")

        if points > maxFLOAT or points <= 0:
            return send_response(400, 26130, {"message":"Points not valid"}, "error")
    else:
        points = None

    newTask, id = await make_task(name=taskName, startDate=startDate, endDate=endDate,guarantor=user.id, file = task, type = type, points = points, deadline = deadline)

    guarantor = {
                "id":user.id,
                "name":user.name,
                "surname": user.surname,
                "abbreviation": user.abbreviation,
                "createdAt": user.createdAt,
                "role": user.role.value,
                "profilePicture":user.profilePicture,
                "email":user.email
                }

    return send_response(201, 26141, {"message":"Task created successfuly", "task":{"id": id, "name": newTask.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor, "deadline": newTask.deadline, "points": newTask.points}}, "success")


@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/add/maturita/guarantor", methods = ["POST"])
async def add_maturita_guarantor():
    taskName = request.form.get("name", None)
    task = request.files.get("task", None)
    idUser = request.form.get("idUser", None)
    idTopic = request.form.get("idTopic", None)

    startDate = datetime.datetime.now(datetime.timezone.utc)
    maturita = Maturita.query.filter((Maturita.endDate > startDate) & (Maturita.startDate < startDate)).order_by(Maturita.id.desc()).first()

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 61010, {"message": "This role can not make maturita with this route"}, "error")
    if not maturita:
        return send_response(400, 61020, {"message": "Cannot make maturita"}, "error")
    if not Evaluator.query.filter_by(idUser = flask_login.current_user.id, idMaturita = maturita.id).first():
        return send_response(400, 61030, {"message": "This user can not be guarantor"}, "error")
    if not taskName:
        return send_response(400, 61040, {"message": "Name not entered"}, "error")
    if not idUser:
        return send_response(400, 61050, {"message": "idUser not entered"}, "error")  
    if not idTopic:
        return send_response(400, 61060, {"message": "idTopic not entered"}, "error")
    
    taskName = str(taskName)

    try:
        idUser = int(idUser)
    except:
        return send_response(400, 61070, {"message":"idUser not integer or is too far"}, "error")
    if idUser > maxINT or idUser <= 0:
        return send_response(400, 61080, {"message":"idUser not valid"}, "error")
    
    user_elaborator = User.query.filter_by(id = idUser).first()

    if not user_elaborator:
        return send_response(400, 61090, {"message": "user not found"}, "error")
    if user_elaborator.role != Role.Student:
        return send_response(400, 61100, {"message": "User with this role can not have assigned tasks"}, "error")
    if User_Team.query.join(Team, (User_Team.idTeam == Team.idTeam) & (User_Team.idTask == Team.idTask) & (User_Team.guarantor == Team.guarantor)).join(Task, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == Task.guarantor)).filter(User_Team.idUser == idUser, Task.type == Type.Maturita, Team.status == Status.Approved, Maturita_Task.idMaturita == maturita.id).first():
        return send_response(400, 61110, {"message": "This user already has maturita task"}, "error")
    try:
        idTopic = int(idTopic)
    except:
        return send_response(400, 61120, {"message":"idTopic not integer or is too far"}, "error")
    if idTopic > maxINT or idTopic <= 0:
        return send_response(400, 61130, {"message":"idTopic not valid"}, "error")
    
    topic = Topic.query.filter_by(id = idTopic).first()

    if not topic:
        return send_response(400, 61140, {"message": "topic not found"}, "error")
    if len(taskName) > 45:
        return send_response(400, 61150, {"message":"Name too long"}, "error")
    if not task:
        return send_response(400, 61160, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
        return send_response(400, 61170, {"message": "Wrong file format or too long"}, "error")
    
    type = Type.Maturita
    user = flask_login.current_user

    await maturita_task_delete(idUser, maturita.id)

    newTask, idTask = await make_task(name=taskName, startDate=startDate, endDate=maturita.endDate, guarantor=user.id, file = task, type = type, points = maturita.maxPoints, deadline = maturita.endDate)

    id = await make_team(idTask = idTask, status = Status.Approved, name = None, isTeam = False, guarantor = flask_login.current_user.id)
    db.session.add(User_Team(idUser, id, idTask, guarantor = user.id))

    maturita_task = Maturita_Task.query.filter_by(idTopic = idTopic, idMaturita = maturita.id).order_by(Maturita_Task.variant.desc()).first()
    variant = 65 if not maturita_task or not maturita_task.variant else ord(maturita_task.variant) + 1
    
    if variant >= 91:
        return send_response(400, 61180, {"message":"Reached max variants for this topic"}, "error")

    db.session.add(Maturita_Task(idTopic = idTopic, idTask = idTask, guarantor = user.id, objector = None, idMaturita = maturita.id, variant = chr(variant)))

    db.session.commit()

    guarantor = {
                "id":user.id,
                "name":user.name,
                "surname": user.surname,
                "abbreviation": user.abbreviation,
                "createdAt": user.createdAt,
                "role": user.role.value,
                "profilePicture":user.profilePicture,
                "email":user.email
                }

    return send_response(201, 61191, {"message":"Task created successfuly", "task":{"id": idTask, "name": newTask.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor, "deadline": newTask.deadline, "points": newTask.points}}, "success")

@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/add/maturita/student", methods = ["POST"])
async def add_maturita_student():
    taskName = request.form.get("name", None)
    task = request.files.get("task", None)
    idUser = request.form.get("idUser", None)
    idTopic = request.form.get("idTopic", None)

    startDate = datetime.datetime.now(datetime.timezone.utc)
    maturita = Maturita.query.filter((Maturita.endDate > startDate) & (Maturita.startDate < startDate)).order_by(Maturita.id.desc()).first()

    if flask_login.current_user.role != Role.Student:
        return send_response(403, 62010, {"message": "This role can not make maturita with this route"}, "error")
    if not maturita:
        return send_response(400, 62020, {"message": "Cannot make maturita"}, "error")
    if User_Team.query.join(Team, (User_Team.idTeam == Team.idTeam) & (User_Team.idTask == Team.idTask) & (User_Team.guarantor == Team.guarantor)).join(Task, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == Task.guarantor)).filter(User_Team.idUser == flask_login.current_user.id, Task.type == Type.Maturita, Team.status == Status.Approved, Maturita_Task.idMaturita == maturita.id).first():
        return send_response(400, 62030, {"message": "Cannot make maturita because this user already has maturita"}, "error")
    if not taskName:
        return send_response(400, 62040, {"message": "Name not entered"}, "error")
    if not idUser:
        return send_response(400, 62050, {"message": "idUser not entered"}, "error")  
    
    taskName = str(taskName)

    try:
        idUser = int(idUser)
    except:
        return send_response(400, 62060, {"message":"idUser not integer or is too far"}, "error")
    if idUser > maxINT or idUser <= 0:
        return send_response(400, 62070, {"message":"idUser not valid"}, "error")
    
    user = User.query.filter_by(id = idUser).first()

    if not user:
        return send_response(400, 62080, {"message": "user not found"}, "error")
    if user.role == Role.Student:
        return send_response(400, 62090, {"message": "User with this role can not be a guarantor"}, "error")
    if not Evaluator.query.filter_by(idUser = user.id, idMaturita = maturita.id).first():
        return send_response(400, 62100, {"message": "This user can not be guarantor"}, "error")
    try:
        idTopic = int(idTopic)
    except:
        return send_response(400, 62110, {"message":"idTopic not integer or is too far"}, "error")
    if idTopic > maxINT or idTopic <= 0:
        return send_response(400, 62120, {"message":"idTopic not valid"}, "error")
    
    topic = Topic.query.filter_by(id = idTopic).first()

    if not topic:
        return send_response(400, 62130, {"message": "topic not found"}, "error")
    if len(taskName) > 45:
        return send_response(400, 62140, {"message":"Name too long"}, "error")
    if not task:
        return send_response(400, 62150, {"message": "Task not entered"}, "error")
    if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
        return send_response(400, 62160, {"message": "Wrong file format or too long"}, "error")
    
    type = Type.Maturita

    newTask, idTask = await make_task(name=taskName, startDate=startDate, endDate=maturita.endDate,guarantor=idUser, file = task, type = type, points = maturita.maxPoints, deadline = maturita.endDate)

    id = await make_team(idTask = idTask, status = Status.Pending, name = None, isTeam = False, guarantor = idUser)
    db.session.add(User_Team(flask_login.current_user.id, id, idTask, idUser))

    db.session.add(Maturita_Task(idTopic = idTopic, idTask = idTask, guarantor = user.id, objector = None, idMaturita = maturita.id, variant = None))
 
    db.session.commit()

    guarantor = {
                "id":user.id,
                "name":user.name,
                "surname": user.surname,
                "abbreviation": user.abbreviation,
                "createdAt": user.createdAt,
                "role": user.role.value,
                "profilePicture":user.profilePicture,
                "email":user.email
                }

    return send_response(201, 62171, {"message":"Task created successfuly", "task":{"id": idTask, "name": newTask.name, "startDate": newTask.startDate, "endDate": newTask.endDate, "task": newTask.task, "guarantor": guarantor, "deadline": newTask.deadline, "points": newTask.points}}, "success")

@flask_login.login_required
@task_bp.route("/task/get/id", methods=["GET"]) 
def get_by_id():
    idTask = request.args.get("id", None)
    guarantor = request.args.get("guarantor", None)
    
    task_data = None

    if not idTask:
        return send_response(400, 30010, {"message": "No id entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 30020, {"message": "Id not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 30030, {"message": "Id not valid"}, "error")
    
    if not guarantor:
        return send_response(400, 30040, {"message": "No guarantor entered"}, "error")
    try:
        guarantor = int(guarantor)
    except:
        return send_response(400, 30050, {"message": "Guarantor not integer"}, "error")
    if guarantor > maxINT or guarantor <=0:
        return send_response(400, 30060, {"message": "Guarantor not valid"}, "error")

    guarantor_user = User.query.filter_by(id = guarantor).first()
    
    if not guarantor_user:
        return send_response(404, 30070, {"message": "Guarantor not found"}, "error")
    
    task = Task.query.filter_by(id=idTask, guarantor = guarantor).first()

    if not task:
        return send_response(404, 30080, {"message": "Task not found"}, "error")

    guarantor_data = {"id":guarantor_user.id, "name":guarantor_user.name, "surname": guarantor_user.surname, "abbreviation": guarantor_user.abbreviation, "createdAt": guarantor_user.createdAt, "role": guarantor_user.role.value, "profilePicture":guarantor_user.profilePicture, "email":guarantor_user.email}

    if task.type == Type.Task:
        task_data = {
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": guarantor_data,
            "points": task.points,
            "deadline": task.deadline
        }
    else:
        user_team = None
        objector_data = []
        maturita_task = Maturita_Task.query.filter_by(idTask = task.id, guarantor = guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = guarantor).first()
        if maturita_task:
            maturita = Maturita.query.filter_by(id = maturita_task.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturita_task.idTopic).first()
            objector = User.query.filter_by(id = maturita_task.objector).first()
            if objector:
                objector_data = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            topic_name = topic.name
            max_points = maturita.maxPoints
        else:
            max_points = None
            topic_name = None
        if team:
            user_team = User_Team.query.filter_by(idTask = task.id, guarantor = guarantor, idTeam = team.id).first()
            idTeam = team.id
        else:
            idTeam = None
        if user_team:
            user = User.query.filter_by(id =user_team.idUser).first()
            user_data = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        else:
            user_data = []

        task_data = {
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": guarantor_data,
            "points": task.points,
            "deadline": task.deadline,
            "user_data":user_data,
            "objector":objector_data,
            "idTeam":idTeam,
            "topic":topic_name,
            "maxPoints":max_points
        }
    
    return send_response(200, 30091, {"message": "Task found", "task": task_data}, "success")

@flask_login.login_required
@task_bp.route("/task/get", methods=["GET"])
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 27010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 27020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 27030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 27040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 27050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 27060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 27070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 27080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        tasks = Task.query.order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber)


    for task in tasks:
        user = User.query.filter_by(id = task.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        all_tasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor, "deadline": task.deadline, "points": task.points})

    return send_response(200, 27091, {"message":"Found tasks", "tasks":all_tasks, "count":count}, "success")

@flask_login.login_required
@task_bp.route("/task/delete", methods=["DELETE"])
async def delete():
    data = request.get_json(force=True)
    idTask = data.get("id", None)
    goodIds = []
    badIds = []

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 28010, {"message":"Students can not delete"}, "error")

    if not idTask:
        return send_response(400, 28020, {"message":"No id entered"}, "error")
    
    if not isinstance(idTask, list):
        idTask = [idTask]
    
    for taskId in idTask:
        try:
            taskId = int(taskId)
        except:
            badIds.append(taskId)
            continue

        if taskId > maxINT or taskId <= 0:
            badIds.append(taskId)
            continue

        task = Task.query.filter_by(id = taskId, guarantor = flask_login.current_user.id).first()

        if not task:
            badIds.append(taskId)
            continue

        if task.type == Type.Maturita:
            maturita = Maturita_Task.query.filter_by(guarantor = flask_login.current_user.id, idTask = taskId).first()

            if maturita:
                db.session.delete(maturita)

        teams = Team.query.filter_by(idTask=taskId).all()
        user_team = User_Team.query.filter_by(idTask=taskId).all()

        for user in user_team:
            db.session.delete(user)

            cancel_reminder(idUser = user.idUser, idTask = taskId, guarantor = flask_login.current_user.id)
        

        for team in teams:
            versions = Version_Team.query.filter_by(idTask = taskId, idTeam = team.idTeam).all()

            for ver in versions:
                db.session.delete(ver)
            db.session.commit()

            db.session.delete(team)
        
        db.session.commit()
        db.session.delete(task)
        await task_delete_sftp(taskId, flask_login.current_user.id)
        goodIds.append(taskId)

    db.session.commit()

    return send_response(200, 28031, {"message":"Tasks deleted", "goodIds":goodIds, "badIds":badIds}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita", methods=["GET"])
def get_maturita():
    idUser = request.args.get("idUser", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 19010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 19020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 19030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 19040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 19050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 19060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 19070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 19080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idUser:
        return send_response(400, 19090, {"message": "No idUser entered"}, "error")
    try:
        idUser = int(idUser)
    except:
        return send_response(400, 19100, {"message": "IdUser not integer"}, "error")
    if idUser > maxINT or idUser <=0:
        return send_response(400, 19110, {"message": "IdUser not valid"}, "error")

    if not searchQuery:
        tasks = Task.query.filter_by(guarantor = idUser, type = Type.Maturita).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.filter_by(guarantor = idUser, type = Type.Maturita).count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = idUser, typeOfSpecialSearch = "maturita")

    for task in tasks:
        user_team = None
        maturita_task = Maturita_Task.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()

        if maturita_task:
            maturita = Maturita.query.filter_by(id = maturita_task.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturita_task.idTopic).first()
            objector = User.query.filter_by(id = maturita_task.objector).first()

            if objector:
                objector_data = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            
            topic_name = topic.name
            max_points = maturita.maxPoints
        else:
            max_points = None
            topic_name = None
            objector_data = []
        if team:
            user_team = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor, idTeam = team.id).first()
            idTeam = team.id
        else:
            idTeam = None
        if user_team:
            user = User.query.filter_by(id =user_team.idUser).first()
            user_data = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        else:
            user_data = []

        all_tasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": task.points,
            "deadline": task.deadline,
            "user_data":user_data,
            "objector":objector_data,
            "idTeam":idTeam,
            "topic":topic_name,
            "maxPoints":max_points
        })
        
    return send_response(200, 19121, {"message": "Found maturitas for guarantor", "tasks": all_tasks, "count": count}, "success")

@flask_login.login_required
@task_bp.route("/task/get/task", methods=["GET"])
def get_task():
    idUser = request.args.get("idUser", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 55010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 55020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 55030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 55040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 55050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 55060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 55070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 55080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idUser:
        return send_response(400, 55090, {"message": "No idUser entered"}, "error")
    try:
        idUser = int(idUser)
    except:
        return send_response(400, 55100, {"message": "IdUser not integer"}, "error")
    if idUser > maxINT or idUser <=0:
        return send_response(400, 55110, {"message": "IdUser not valid"}, "error")

    if not searchQuery:
        tasks = Task.query.filter_by(guarantor = idUser, type = Type.Task).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.filter_by(guarantor = idUser, type = Type.Task).count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = idUser, typeOfSpecialSearch = "task")

    for task in tasks:
        all_tasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": task.guarantor,
            "deadline": task.deadline,
            "points":task.points
        })
        
    return send_response(200, 55121, {"message": "Found tasks for guarantor", "tasks": all_tasks, "count": count}, "success")


@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/update", methods=["PUT"])
async def update():
    idTask = request.form.get("id",None)
    taskName = request.form.get("name", None)
    endDate = request.form.get("endDate", None)
    task = request.files.get("task", None)
    deadline = request.form.get("deadline", None)
    points = request.form.get("points", None)

    if flask_login.current_user.role == Role.Student:
        return send_response(400, 74010, {"message": "This role can not update task"}, "error")
    if not idTask:
        return send_response(400, 74020, {"message": "No id entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 74030, {"message": "Id not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 74040, {"message": "Id not valid"}, "error")
    
    actual_task = Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).first()

    if not actual_task:
       return send_response(403, 74050, {"message": "No task found"}, "error")
    
    if taskName:
        taskName = str(taskName)

        if len(taskName) > 45:
            return send_response(400, 74060, {"message":"Name too long"}, "error")
        actual_task.name = taskName

    if task:
        if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
            return send_response(400, 74070, {"message": "Wrong file format or too long"}, "error")
        
        await update_task(file = task, id = idTask, guarantor = flask_login.current_user.id, file2 = actual_task.task)
        actual_task.task = task.filename
        
    
    if actual_task.type == Type.Task:
        if endDate:
            try:
                endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
            except:
                return send_response(400, 74080, {"message":"End date not integer or is too far"}, "error")
            if endDate <= actual_task.startDate.replace(tzinfo = datetime.timezone.utc):
                return send_response(400, 74090, {"message":"Ending before begining"}, "error")
            actual_task.endDate = endDate

        user = flask_login.current_user

        if deadline:
            try:
                deadline = datetime.datetime.fromtimestamp(int(deadline)/1000, tz=datetime.timezone.utc)

                if deadline < actual_task.startDate.replace(tzinfo = datetime.timezone.utc):
                    return send_response(400, 74100, {"message":"Deadline before startDate"}, "error")
                if deadline < actual_task.endDate.replace(tzinfo = datetime.timezone.utc):
                    return send_response(400, 74110, {"message":"Deadline before endDate"}, "error")
            except:
                return send_response(400, 74120, {"message":"Deadline not integer or is too far"}, "error")
            
            actual_task.deadline = deadline
        if points:
            try:
                points = float(points)
            except:
                return send_response(400, 74130, {"message":"Points are not float"}, "error")

            if points > maxFLOAT or points <= 0:
                return send_response(400, 74140, {"message":"Points not valid"}, "error")
            
            actual_task.points = points

    db.session.commit()

    guarantor = {
                "id":user.id,
                "name":user.name,
                "surname": user.surname,
                "abbreviation": user.abbreviation,
                "createdAt": user.createdAt,
                "role": user.role.value,
                "profilePicture":user.profilePicture,
                "email":user.email
                }

    return send_response(201, 74151, {"message":"Task updated successfuly", "task":{"id": idTask, "name": actual_task.name, "startDate": actual_task.startDate, "endDate": actual_task.endDate, "task": actual_task.task, "guarantor": guarantor, "deadline": actual_task.deadline, "points": actual_task.points}}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita/approved", methods=["GET"])
def get_maturita_approved():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 75010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 75020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 75030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 75040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 75050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 75060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 75070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 75080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not searchQuery:
        tasks = Task.query.join(Team, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).filter(Task.guarantor == flask_login.current_user.id, Task.type == Type.Maturita, Team.status == Status.Approved).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.join(Team, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).filter(Task.guarantor == flask_login.current_user.id, Task.type == Type.Maturita, Team.status == Status.Approved).count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = flask_login.current_user.id, typeOfSpecialSearch = "maturita", status=Status.Approved)

    for task in tasks:
        user_team = None
        maturita_task = Maturita_Task.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()

        if maturita_task:
            maturita = Maturita.query.filter_by(id = maturita_task.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturita_task.idTopic).first()
            objector = User.query.filter_by(id = maturita_task.objector).first()

            if objector:
                objector_data = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            
            topic_name = topic.name
            max_points = maturita.maxPoints
        else:
            max_points = None
            topic_name = None
            objector_data = []
        if team:
            user_team = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor, idTeam = team.id).first()
            idTeam = team.id
            review = team.review
            reviewUpdatedAt = team.reviewUpdatedAt
        else:
            idTeam = None
            review = None
            reviewUpdatedAt = None
        if user_team:
            user = User.query.filter_by(id =user_team.idUser).first()
            user_data = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        else:
            user_data = []

        all_tasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": task.points,
            "deadline": task.deadline,
            "user_data":user_data,
            "objector":objector_data,
            "idTeam":idTeam,
            "topic":topic_name,
            "maxPoints":max_points,
            "review":review,
            "reviewUpdatedAt":reviewUpdatedAt
        })
        
    return send_response(200, 75091, {"message": "Found approved maturitas for guarantor", "tasks": all_tasks, "count": count}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita/pending", methods=["GET"])
def get_maturita_pending():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    all_tasks = []

    if not amountForPaging:
        return send_response(400, 76010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 76020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 76030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 76040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 76050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 76060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 76070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 76080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not searchQuery:
        tasks = Task.query.join(Team, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).filter(Task.guarantor == flask_login.current_user.id, Task.type == Type.Maturita, Team.status == Status.Pending).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.join(Team, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor)).filter(Task.guarantor == flask_login.current_user.id, Task.type == Type.Maturita, Team.status == Status.Pending).count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = flask_login.current_user.id, typeOfSpecialSearch = "maturita", status=Status.Pending)

    for task in tasks:
        user_team = None
        maturita_task = Maturita_Task.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()

        if maturita_task:
            maturita = Maturita.query.filter_by(id = maturita_task.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturita_task.idTopic).first()
            objector = User.query.filter_by(id = maturita_task.objector).first()

            if objector:
                objector_data = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            
            topic_name = topic.name
            max_points = maturita.maxPoints
        else:
            max_points = None
            topic_name = None
            objector_data = []
        if team:
            user_team = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor, idTeam = team.id).first()
            idTeam = team.id
            status = team.status
        else:
            idTeam = None
            status = None
        if user_team:
            user = User.query.filter_by(id =user_team.idUser).first()
            user_data = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        else:
            user_data = []

        all_tasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": task.points,
            "deadline": task.deadline,
            "user_data":user_data,
            "objector":objector_data,
            "idTeam":idTeam,
            "topic":topic_name,
            "maxPoints":max_points,
            "status":status
        })
        
    return send_response(200, 76091, {"message": "Found pending maturitas for guarantor", "tasks": all_tasks, "count": count}, "success")