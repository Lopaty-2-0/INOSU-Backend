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
from src.utils.paging import task_paging, maturita_task_paging
from src.utils.team import make_team
from app import db, max_INT, max_FLOAT
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

    if len(taskName) > 255:
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

        if points > max_FLOAT or points <= 0:
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
    if idUser > max_INT or idUser <= 0:
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
    if idTopic > max_INT or idTopic <= 0:
        return send_response(400, 61130, {"message":"idTopic not valid"}, "error")
    
    topic = Topic.query.filter_by(id = idTopic).first()

    if not topic:
        return send_response(400, 61140, {"message": "topic not found"}, "error")
    if len(taskName) > 255:
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

    maturitaTask = Maturita_Task.query.filter_by(idTopic = idTopic, idMaturita = maturita.id).order_by(Maturita_Task.variant.desc()).first()
    variant = 65 if not maturitaTask or not maturitaTask.variant else ord(maturitaTask.variant) + 1
    
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
    if idUser > max_INT or idUser <= 0:
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
    if idTopic > max_INT or idTopic <= 0:
        return send_response(400, 62120, {"message":"idTopic not valid"}, "error")
    
    topic = Topic.query.filter_by(id = idTopic).first()

    if not topic:
        return send_response(400, 62130, {"message": "topic not found"}, "error")
    if len(taskName) > 255:
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
    
    taskData = None

    if not idTask:
        return send_response(400, 30010, {"message": "No id entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 30020, {"message": "Id not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 30030, {"message": "Id not valid"}, "error")
    
    if not guarantor:
        return send_response(400, 30040, {"message": "No guarantor entered"}, "error")
    try:
        guarantor = int(guarantor)
    except:
        return send_response(400, 30050, {"message": "Guarantor not integer"}, "error")
    if guarantor > max_INT or guarantor <=0:
        return send_response(400, 30060, {"message": "Guarantor not valid"}, "error")

    guarantorUser = User.query.filter_by(id = guarantor).first()
    
    if not guarantorUser:
        return send_response(404, 30070, {"message": "Guarantor not found"}, "error")
    
    task = Task.query.filter_by(id=idTask, guarantor = guarantor).first()

    if not task:
        return send_response(404, 30080, {"message": "Task not found"}, "error")

    guarantorData = {"id":guarantorUser.id, "name":guarantorUser.name, "surname": guarantorUser.surname, "abbreviation": guarantorUser.abbreviation, "createdAt": guarantorUser.createdAt, "role": guarantorUser.role.value, "profilePicture":guarantorUser.profilePicture, "email":guarantorUser.email}

    if task.type == Type.Task:
        taskData = {
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": guarantorData,
            "points": task.points,
            "deadline": task.deadline
        }
    else:
        userTeam = None
        objectorData = []
        maturitaTask = Maturita_Task.query.filter_by(idTask = task.id, guarantor = guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = guarantor).first()
        if maturitaTask:
            maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
            objector = User.query.filter_by(id = maturitaTask.objector).first()
            if objector:
                objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            topicName = topic.name
            maxPoints = maturita.maxPoints
        else:
            maxPoints = None
            topicName = None
        if team:
            userTeam = User_Team.query.filter_by(idTask = task.id, guarantor = guarantor, idTeam = team.idTeam).first()
            idTeam = team.idTeam
        else:
            idTeam = None
        if userTeam:
            user = User.query.filter_by(id =userTeam.idUser).first()
            userData = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}
        else:
            userData = []

        taskData = {
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": guarantorData,
            "points": task.points,
            "deadline": task.deadline,
            "userData":userData,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints
        }
    
    return send_response(200, 30091, {"message": "Task found", "task": taskData}, "success")

@flask_login.login_required
@task_bp.route("/task/get", methods=["GET"])
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allTasks = []

    if not amountForPaging:
        return send_response(400, 27010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 27020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 27030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 27040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 27050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 27060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
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
        allTasks.append({"id": task.id, "name": task.name, "startDate": task.startDate, "endDate": task.endDate, "task": task.task, "guarantor": guarantor, "deadline": task.deadline, "points": task.points})

    return send_response(200, 27091, {"message":"Found tasks", "tasks":allTasks, "count":count}, "success")

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

        if taskId > max_INT or taskId <= 0:
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

        teams = Team.query.filter_by(idTask=taskId, guarantor = flask_login.current_user.id).all()
        userTeam = User_Team.query.filter_by(idTask=taskId, guarantor = flask_login.current_user.id).all()

        for user in userTeam:
            db.session.delete(user)

            cancel_reminder(idUser = user.idUser, idTask = taskId, guarantor = flask_login.current_user.id)
        

        for team in teams:
            versions = Version_Team.query.filter_by(idTask = taskId, idTeam = team.idTeam, guarantor = flask_login.current_user.id).all()

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

    allTasks = []

    now = datetime.datetime.now(tz = datetime.timezone.utc)

    if not amountForPaging:
        return send_response(400, 19010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 19020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 19030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 19040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 19050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 19060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
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
    if idUser > max_INT or idUser <=0:
        return send_response(400, 19110, {"message": "IdUser not valid"}, "error")
    
    maturita = Maturita.query.filter(Maturita.endDate >= now, now >= Maturita.startDate).first()

    if not maturita:
        tasks = []
        count = 0
    else:
        if not searchQuery:
            tasks = Task.query.join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == idUser) & (Maturita_Task.idMaturita == maturita.id)).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Task.query.join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == idUser) & (Maturita_Task.idMaturita == maturita.id)).count()
        else:
            tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = idUser, typeOfSpecialSearch = "maturita", idMaturita = maturita.id)

    for task in tasks:
        userTeam = None
        objectorData = []
        maxPoints = None
        topicName = None
        idTeam = None
        userData = []
        maturitaTask = Maturita_Task.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()

        if maturitaTask:
            maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
            objector = User.query.filter_by(id = maturitaTask.objector).first()

            if objector:
                objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            
            topicName = topic.name
            maxPoints = maturita.maxPoints
            
        if team:
            userTeam = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor, idTeam = team.idTeam).first()
            idTeam = team.idTeam

        if userTeam:
            user = User.query.filter_by(id =userTeam.idUser).first()
            userData = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}


        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": task.points,
            "deadline": task.deadline,
            "userData":userData,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints
        })
        
    return send_response(200, 19121, {"message": "Found maturitas for guarantor", "tasks": allTasks, "count": count}, "success")

@flask_login.login_required
@task_bp.route("/task/get/task", methods=["GET"])
def get_task():
    idUser = request.args.get("idUser", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allTasks = []

    if not amountForPaging:
        return send_response(400, 55010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 55020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 55030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 55040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 55050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 55060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
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
    if idUser > max_INT or idUser <=0:
        return send_response(400, 55110, {"message": "IdUser not valid"}, "error")

    if not searchQuery:
        tasks = Task.query.filter_by(guarantor = idUser, type = Type.Task).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Task.query.filter_by(guarantor = idUser, type = Type.Task).count()
    else:
        tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = idUser, typeOfSpecialSearch = "task")

    for task in tasks:
        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "guarantor": task.guarantor,
            "deadline": task.deadline,
            "points":task.points
        })
        
    return send_response(200, 55121, {"message": "Found tasks for guarantor", "tasks": allTasks, "count": count}, "success")


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
    objector = request.form.get("objector", None)

    if flask_login.current_user.role == Role.Student:
        return send_response(400, 74010, {"message": "This role can not update task"}, "error")
    if not idTask:
        return send_response(400, 74020, {"message": "No id entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 74030, {"message": "Id not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 74040, {"message": "Id not valid"}, "error")
    
    actualTask = Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).first()

    if not actualTask:
       return send_response(403, 74050, {"message": "No task found"}, "error")
    
    if taskName:
        taskName = str(taskName)

        if len(taskName) > 255:
            return send_response(400, 74060, {"message":"Name too long"}, "error")
        actualTask.name = taskName

    if task:
        if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
            return send_response(400, 74070, {"message": "Wrong file format or too long"}, "error")
        
        await update_task(file = task, id = idTask, guarantor = flask_login.current_user.id, file2 = actualTask.task)
        actualTask.task = task.filename
        
    
    if actualTask.type == Type.Task:
        if endDate:
            try:
                endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
            except:
                return send_response(400, 74080, {"message":"End date not integer or is too far"}, "error")
            if endDate <= actualTask.startDate.replace(tzinfo = datetime.timezone.utc):
                return send_response(400, 74090, {"message":"Ending before begining"}, "error")
            actualTask.endDate = endDate

        if deadline:
            try:
                deadline = datetime.datetime.fromtimestamp(int(deadline)/1000, tz=datetime.timezone.utc)

                if deadline < actualTask.startDate.replace(tzinfo = datetime.timezone.utc):
                    return send_response(400, 74100, {"message":"Deadline before startDate"}, "error")
                if deadline < actualTask.endDate.replace(tzinfo = datetime.timezone.utc):
                    return send_response(400, 74110, {"message":"Deadline before endDate"}, "error")
            except:
                return send_response(400, 74120, {"message":"Deadline not integer or is too far"}, "error")
            
            actualTask.deadline = deadline
        if points:
            try:
                points = float(points)
            except:
                return send_response(400, 74130, {"message":"Points are not float"}, "error")

            if points > max_FLOAT or points <= 0:
                return send_response(400, 74140, {"message":"Points not valid"}, "error")
            
            actualTask.points = points
    else:
        maturita = Maturita_Task.query.filter_by(idTask = idTask, guarantor = flask_login.current_user.id).first()

        if objector:
            try:
                objector = int(objector)
            except:
                return send_response(400, 74150, {"message": "objector not integer"}, "error")
            if objector > max_INT or objector <=0:
                return send_response(400, 74160, {"message": "objector not valid"}, "error")
            
            actualObjector = User.query.filter_by(id = objector).first()
            evaluator = Evaluator.query.filter_by(idUser = objector, idMaturita = maturita.idMaturita).first()

            if not actualObjector:
                return send_response(400, 74170, {"message": "objector not valid"}, "error")
            if not evaluator:
                return send_response(400, 74180, {"message": "objector not valid"}, "error")
            if flask_login.current_user.id == actualObjector.id:
                return send_response(400, 74190, {"message": "cannot object  this task"}, "error")
            
            maturita.objector = objector
            
    db.session.commit()

    return send_response(201, 74201, {"message":"Task updated successfuly"}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita/guarantor/approved", methods=["GET"])
def get_maturita_guarantor_approved():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    now = datetime.datetime.now(tz=datetime.timezone.utc)

    allTasks = []

    if not amountForPaging:
        return send_response(400, 75010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 75020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 75030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 75040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 75050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 75060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 75070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 75080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    maturita = Maturita.query.filter(Maturita.endDate >= now, now >= Maturita.startDate).first()

    if not maturita:
        tasks = []
        count = 0
    else:
        if not searchQuery:
            tasks = Task.query.join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == flask_login.current_user.id) & (Maturita_Task.idMaturita == maturita.id)).join(Team, (Team.idTask == Task.id) & (Team.guarantor == flask_login.current_user.id)).filter(Team.status == Status.Approved).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Task.query.join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == flask_login.current_user.id) & (Maturita_Task.idMaturita == maturita.id)).join(Team, (Team.idTask == Task.id) & (Team.guarantor == flask_login.current_user.id)).filter(Team.status == Status.Approved).count()
        else:
            tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = flask_login.current_user.id, typeOfSpecialSearch = "maturita", status=Status.Approved, idMaturita = maturita.id)

    for task in tasks:
        userTeam = None
        objectorData = []
        maxPoints = None
        topicName = None
        idTeam = None
        userData = []
        points = None
        maturitaTask = Maturita_Task.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()

        if maturitaTask:
            maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
            objector = User.query.filter_by(id = maturitaTask.objector).first()

            if objector:
                objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            
            topicName = topic.name
            maxPoints = maturita.maxPoints
            
        if team:
            userTeam = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor, idTeam = team.idTeam).first()
            idTeam = team.idTeam
            points = team.points

        if userTeam:
            user = User.query.filter_by(id =userTeam.idUser).first()
            userData = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}


        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": points,
            "deadline": task.deadline,
            "userData":userData,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints
        })
        
    return send_response(200, 75091, {"message": "Found approved maturitas for guarantor", "tasks": allTasks, "count": count}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita/guarantor/pending", methods=["GET"])
def get_maturita_guarantor_pending():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allTasks = []

    now = datetime.datetime.now(datetime.timezone.utc)

    if not amountForPaging:
        return send_response(400, 76010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 76020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 76030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 76040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 76050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 76060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 76070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 76080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    maturita = Maturita.query.filter(Maturita.endDate >= now, now >= Maturita.startDate).first()

    if not maturita:
        tasks = []
        count = 0
    else:
        if not searchQuery:
            tasks = Task.query.join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == flask_login.current_user.id) & (Maturita_Task.idMaturita == maturita.id)).join(Team, (Team.idTask == Task.id) & (Team.guarantor == flask_login.current_user.id)).filter(Team.status == Status.Pending).order_by(Task.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Task.query.join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == flask_login.current_user.id) & (Maturita_Task.idMaturita == maturita.id)).join(Team, (Team.idTask == Task.id) & (Team.guarantor == flask_login.current_user.id)).filter(Team.status == Status.Pending).count()
        else:
            tasks, count = task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, specialSearch = flask_login.current_user.id, typeOfSpecialSearch = "maturita", status=Status.Pending, idMaturita = maturita.id)
    
    for task in tasks:
        userTeam = None
        objectorData = []
        maxPoints = None
        topicName = None
        idTeam = None
        userData = []
        points = None
        maturitaTask = Maturita_Task.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()

        if maturitaTask:
            maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
            topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
            objector = User.query.filter_by(id = maturitaTask.objector).first()

            if objector:
                objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
            
            topicName = topic.name
            maxPoints = maturita.maxPoints
            
        if team:
            userTeam = User_Team.query.filter_by(idTask = task.id, guarantor = task.guarantor, idTeam = team.idTeam).first()
            idTeam = team.idTeam
            points = team.points

        if userTeam:
            user = User.query.filter_by(id =userTeam.idUser).first()
            userData = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}


        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": points,
            "deadline": task.deadline,
            "userData":userData,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints
        })
        
    return send_response(200, 76091, {"message": "Found pending maturitas for guarantor", "tasks": allTasks, "count": count}, "success")

@task_bp.route("/task/get/maturita/student/approved", methods = ["GET"])
@flask_login.login_required
def get_maturita_student_approved():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    maturita = Maturita.query.filter(Maturita.endDate >= now, Maturita.startDate <= now).first()

    if not maturita:
        return send_response(400, 78010, {"message": "No current maturita"}, "error")
    
    maturitaTask = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status == Status.Approved)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).first()

    if not maturitaTask:
        return send_response(400, 78020, {"message": "This user doesnt have approved maturita task"}, "error")
    
    objectorData = []
    maxPoints = None
    topicName = None
    idTeam = None
    userData = []
    points = None
    task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
    team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
    maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
    topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
    objector = User.query.filter_by(id = maturitaTask.objector).first()
    user = User.query.filter_by(id = maturitaTask.guarantor).first()

    if objector:
        objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
    
    topicName = topic.name
    maxPoints = maturita.maxPoints
        
    if team:
        idTeam = team.idTeam
        points = team.points

    userData = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}


    actualTask = {
        "id": task.id,
        "name": task.name,
        "startDate": task.startDate,
        "endDate": task.endDate,
        "task": task.task,
        "points": points,
        "deadline": task.deadline,
        "guarantor":userData,
        "objector":objectorData,
        "idTeam":idTeam,
        "topic":topicName,
        "maxPoints":maxPoints
    }

    return send_response(200, 78031, {"message": "Found approved maturita for user", "task": actualTask}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita/student/pending", methods=["GET"])
def get_maturita_student_pending():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allTasks = []

    now = datetime.datetime.now(datetime.timezone.utc)

    if not amountForPaging:
        return send_response(400, 79010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 79020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 79030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 79040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 79050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 79060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 79070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 79080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    maturita = Maturita.query.filter(Maturita.endDate >= now, now >= Maturita.startDate).first()

    if not maturita:
        maturitaTasks = []
        count = 0
    else:
        if not searchQuery:
            maturitaTasks = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status == Status.Pending)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).filter(Maturita_Task.idMaturita == maturita.id).order_by(Maturita_Task.idTask.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status == Status.Pending)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).filter(Maturita_Task.idMaturita == maturita.id).count()
        else:
            maturitaTasks, count = maturita_task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, idUser = flask_login.current_user.id, idMaturita = maturita.id, status = Status.Pending)
    
    for maturitaTask in maturitaTasks:
        objectorData = []
        maxPoints = None
        topicName = None
        idTeam = None
        points = None
        guarantor = []
        task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
        topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
        objector = User.query.filter_by(id = maturitaTask.objector).first()

        if objector:
            objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
        
        if topic:
            topicName = topic.name
        if maturita:
            maxPoints = maturita.maxPoints
        
        if team:
            idTeam = team.idTeam
            points = team.points

        user = User.query.filter_by(id = maturitaTask.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}


        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": points,
            "deadline": task.deadline,
            "guarantor":guarantor,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints
        })
        
    return send_response(200, 79091, {"message": "Found pending maturitas for student", "tasks": allTasks, "count": count}, "success")

@flask_login.login_required
@check_file_size(32*1024*1024)
@task_bp.route("/task/update/maturita/student", methods=["PUT"])
async def update_maturita_student():
    idTask = request.form.get("id",None)
    taskName = request.form.get("name", None)
    task = request.files.get("task", None)
    guarantor = request.form.get("guarantor", None)

    now = datetime.datetime.now(tz=datetime.timezone.utc)
    maturita = Maturita.query.filter(Maturita.startDate <= now, Maturita.endDate >= now).first()

    if not idTask:
        return send_response(400, 80010, {"message": "No id entered"}, "error")
    if not guarantor:
        return send_response(400, 80020, {"message": "No guarantor entered"}, "error")
    if not maturita:
        return send_response(400, 80030, {"message": "No maturita found"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 80040, {"message": "Id not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 80050, {"message": "Id not valid"}, "error")
    try:
        guarantor = int(guarantor)
    except:
        return send_response(400, 80060, {"message": "Id not integer"}, "error")
    if guarantor > max_INT or guarantor <=0:
        return send_response(400, 80070, {"message": "Id not valid"}, "error")
    
    user = User.query.filter_by(id = guarantor).first()
    
    if not user:
        return send_response(403, 80080, {"message": "No guarantor found"}, "error")
    
    actualTask = Task.query.join(Team, (Team.idTask == Task.id) & (Team.guarantor == Task.guarantor) & (Team.status == Status.Pending)).join(User_Team, (User_Team.idTask == Task.id) & (User_Team.guarantor == Task.guarantor) & (User_Team.idUser == flask_login.current_user.id) & (User_Team.idTeam == Team.idTeam)).join(Maturita_Task, (Maturita_Task.idTask == Task.id) & (Maturita_Task.guarantor == Task.guarantor) & (Maturita_Task.idMaturita == maturita.id)).filter(Task.id == idTask, Task.guarantor == guarantor).first()

    if not actualTask:
       return send_response(403, 80090, {"message": "No task found"}, "error")
    
    if taskName:
        taskName = str(taskName)

        if len(taskName) > 255:
            return send_response(400, 80100, {"message":"Name too long"}, "error")
        actualTask.name = taskName

    if task:
        if not task.filename.rsplit(".", 1)[1].lower() in task_extensions or len(task.filename) > 255:
            return send_response(400, 80110, {"message": "Wrong file format or too long"}, "error")
        
        await update_task(file = task, id = idTask, guarantor = guarantor, file2 = actualTask.task)
        actualTask.task = task.filename
    
    db.session.commit()

    return send_response(201, 80121, {"message":"Task updated successfuly"}, "success")


@flask_login.login_required
@task_bp.route("/task/delete/student", methods=["DELETE"])
async def delete_student():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    guarantor = data.get("guarantor", None)
    goodIds = []
    badIds = []

    if flask_login.current_user.role != Role.Student:
        return send_response(403, 81010, {"message":"This route is not used for this role"}, "error")

    if not idTask:
        return send_response(400, 81020, {"message":"No idTask entered"}, "error")
    if not guarantor:
        return send_response(400, 81030, {"message":"No guarantor entered"}, "error")
    
    if not isinstance(idTask, list):
        idTask = [idTask]

    if not isinstance(guarantor, list):
        guarantor = [guarantor]

    if not len(idTask) == len(guarantor):
        return send_response(400, 81040, {"message":"Not correct amount of guarantor for idTask"}, "error")
    
    for i in range(len(idTask)):
        taskId = idTask[i]
        guarantorId = guarantor[i]
        try:
            taskId = int(taskId)
        except:
            badIds.append(taskId)
            continue

        if taskId > max_INT or taskId <= 0:
            badIds.append(taskId)
            continue

        try:
            guarantorId = int(guarantorId)
        except:
            badIds.append(taskId)
            continue

        if guarantorId > max_INT or guarantorId <= 0:
            badIds.append(taskId)
            continue

        task = Task.query.join(Team, (Team.idTask == taskId) & (Team.guarantor == guarantorId) & (Team.status != Status.Approved)).join(User_Team,(User_Team.idUser == flask_login.current_user.id) & (User_Team.idTask == taskId) & (User_Team.guarantor == guarantorId) & (User_Team.idTeam == Team.idTeam)).filter(Task.type == Type.Maturita, Task.id == taskId, Task.guarantor == guarantorId).first()

        if not task:
            badIds.append(taskId)
            continue
        
        maturita = Maturita_Task.query.filter_by(guarantor = guarantorId, idTask = taskId).first()

        if maturita:
            db.session.delete(maturita)

        team = Team.query.filter_by(idTask=taskId, guarantor = guarantorId).first()
        userTeam = User_Team.query.filter_by(idTask=taskId, guarantor = guarantorId).first()

        db.session.delete(userTeam)

        cancel_reminder(idUser = flask_login.current_user.id, idTask = taskId, guarantor = guarantorId)
        
        db.session.commit()

        db.session.delete(team)
        
        db.session.commit()
        db.session.delete(task)
        await task_delete_sftp(taskId, guarantorId)
        goodIds.append(taskId)

    db.session.commit()

    return send_response(200, 81051, {"message":"Tasks deleted", "goodIds":goodIds, "badIds":badIds}, "success")

@flask_login.login_required
@task_bp.route("/task/get/maturita/student/rejected", methods=["GET"])
def get_maturita_student_rejected():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allTasks = []

    now = datetime.datetime.now(datetime.timezone.utc)

    if not amountForPaging:
        return send_response(400, 82010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 82020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 82030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 82040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 82050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 82060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 82070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 82080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    maturita = Maturita.query.filter(Maturita.endDate >= now, now >= Maturita.startDate).first()

    if not maturita:
        maturitaTasks = []
        count = 0
    else:
        if not searchQuery:
            maturitaTasks = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status == Status.Rejected)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).filter(Maturita_Task.idMaturita == maturita.id).order_by(Maturita_Task.idTask.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status == Status.Rejected)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).filter(Maturita_Task.idMaturita == maturita.id).count()
        else:
            maturitaTasks, count = maturita_task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, idUser = flask_login.current_user.id, idMaturita = maturita.id, status = Status.Rejected)
    
    for maturitaTask in maturitaTasks:
        objectorData = []
        maxPoints = None
        topicName = None
        idTeam = None
        points = None
        guarantor = []
        task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
        topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
        objector = User.query.filter_by(id = maturitaTask.objector).first()

        if objector:
            objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
        
        if topic:
            topicName = topic.name
        if maturita:
            maxPoints = maturita.maxPoints
        
        if team:
            idTeam = team.idTeam
            points = team.points

        user = User.query.filter_by(id = maturitaTask.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}


        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": points,
            "deadline": task.deadline,
            "guarantor":guarantor,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints
        })
        
    return send_response(200, 82091, {"message": "Found rejected maturitas for student", "tasks": allTasks, "count": count}, "success")


@flask_login.login_required
@task_bp.route("/task/get/maturita/student/not_approved", methods=["GET"])
def get_maturita_student_not_approved():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allTasks = []

    now = datetime.datetime.now(datetime.timezone.utc)

    if not amountForPaging:
        return send_response(400, 40010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 40020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 40030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 40040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 40050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 40060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 40070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 40080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    maturita = Maturita.query.filter(Maturita.endDate >= now, now >= Maturita.startDate).first()

    if not maturita:
        maturitaTasks = []
        count = 0
    else:
        if not searchQuery:
            maturitaTasks = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status != Status.Approved)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).filter(Maturita_Task.idMaturita == maturita.id).order_by(Maturita_Task.idTask.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Maturita_Task.query.join(Team, (Team.idTask == Maturita_Task.idTask) & (Team.guarantor == Maturita_Task.guarantor) & (Team.status != Status.Approved)).join(User_Team, (User_Team.idTask == Maturita_Task.idTask) & (User_Team.guarantor == Maturita_Task.guarantor) & (User_Team.idUser == flask_login.current_user.id)).filter(Maturita_Task.idMaturita == maturita.id).count()
        else:
            maturitaTasks, count = maturita_task_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber, idUser = flask_login.current_user.id, idMaturita = maturita.id)
    
    for maturitaTask in maturitaTasks:
        objectorData = []
        maxPoints = None
        topicName = None
        idTeam = None
        points = None
        status = None
        guarantor = []
        task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
        team = Team.query.filter_by(idTask = task.id, guarantor = task.guarantor).first()
        maturita = Maturita.query.filter_by(id = maturitaTask.idMaturita).first()  
        topic = Topic.query.filter_by(id = maturitaTask.idTopic).first()
        objector = User.query.filter_by(id = maturitaTask.objector).first()

        if objector:
            objectorData = {"id":objector.id, "name":objector.name, "surname": objector.surname, "abbreviation": objector.abbreviation, "createdAt": objector.createdAt, "role": objector.role.value, "profilePicture":objector.profilePicture, "email":objector.email, "updatedAt":objector.updatedAt}
        
        if topic:
            topicName = topic.name
        if maturita:
            maxPoints = maturita.maxPoints
        
        if team:
            idTeam = team.idTeam
            points = team.points
            status = team.status.value

        user = User.query.filter_by(id = maturitaTask.guarantor).first()
        guarantor = {"id":user.id, "name":user.name, "surname": user.surname, "abbreviation": user.abbreviation, "createdAt": user.createdAt, "role": user.role.value, "profilePicture":user.profilePicture, "email":user.email, "updatedAt":user.updatedAt}

        allTasks.append({
            "id": task.id,
            "name": task.name,
            "startDate": task.startDate,
            "endDate": task.endDate,
            "task": task.task,
            "points": points,
            "deadline": task.deadline,
            "guarantor":guarantor,
            "objector":objectorData,
            "idTeam":idTeam,
            "topic":topicName,
            "maxPoints":maxPoints,
            "status":status
        })
        
    return send_response(200, 40091, {"message": "Found not approved maturitas for guarantor", "tasks": allTasks, "count": count}, "success")
