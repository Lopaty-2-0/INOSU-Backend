from flask import Blueprint, request, send_file
from src.models.Maturita import Maturita
from src.models.Maturita_Task import Maturita_Task
from src.models.Evaluator import Evaluator
from src.models.Task import Task
from src.models.Team import Team
from src.utils.reminder import cancel_reminder
from src.utils.archive_conversation import cancel_archive_conversation
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from src.models.Conversation import Conversation
from src.models.User import User
import flask_login
from src.utils.enums import Role
from src.utils.response import send_response
from src.utils.paging import maturita_paging
from app import db, max_FLOAT, max_INT
import datetime
from src.utils.task import delete_upload_task
from src.utils.version import delete_upload_version
from src.utils.check_file import check_file_size
import json
import io

#TODO: přidat export + import (json)

maturita_bp = Blueprint("maturita", __name__)

@maturita_bp.route("/maturita/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 67010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    maxPoints = data.get("maxPoints", None)
    startDate = data.get("startDate", None)
    endDate = data.get("endDate", None)
    evaluators = data.get("evaluators", None)

    goodIds = []
    badIds = []

    if not grade:
        return send_response(400, 67020, {"message": "grade missing"}, "error")
    if not maxPoints:
         return send_response(400, 67030, {"message": "maxPoints missing"}, "error")
    if not startDate:
         return send_response(400, 67040, {"message": "startDate missing"}, "error")
    if not endDate:
         return send_response(400, 67050, {"message": "endDate missing"}, "error")
    
    grade = str(grade)

    if len(grade) > 9:
            return send_response(400, 67060, {"message": "grade too long"}, "error")
    if Maturita.query.filter_by(grade = grade).first():
        return send_response(400, 67070, {"message": "grade already in use"}, "error")
    
    try:
        maxPoints = float(maxPoints)
    except:
        return send_response(400, 67080, {"message":"maxPoints not float"}, "error")
    if maxPoints > max_FLOAT or maxPoints <= 0:
        return send_response(400, 67090, {"message": "maxPoints not valid"}, "error")  
    try:
        endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 67100, {"message":"End date not integer or is too far"}, "error")
    try:
        startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
    except:
        return send_response(400, 67110, {"message":"startDate not integer or is too far"}, "error")
    if endDate <= startDate:
        return send_response(400, 67120, {"message":"Ending before begining"}, "error")
    
    newMaturita = Maturita(grade = grade, maxPoints = maxPoints, startDate = startDate, endDate = endDate)
    db.session.add(newMaturita)
    db.session.commit()

    if evaluators:
        if not isinstance(evaluators, list):
            evaluators = [evaluators]
        
        for evaluator in evaluators:
            try:
                evaluator = int(evaluator)
            except:
                badIds.append(evaluator)
                continue

            if evaluator > max_INT or evaluator <= 0:
                badIds.append(evaluator)
                continue

            user = User.query.filter_by(id = evaluator).first()

            if not user or user.role == Role.Student:
                badIds.append(evaluator)
                continue

            db.session.add(Evaluator(idUser = evaluator, idMaturita = newMaturita.id))
            goodIds.append(evaluator)

        db.session.commit()

    return send_response (201, 67131, {"message": "maturita created successfuly", "maturita":{"grade":newMaturita.grade, "id":newMaturita.id, "maxPoints":newMaturita.maxPoints, "startDate":newMaturita.startDate, "endDate":newMaturita.endDate}, "goodIds":goodIds, "badIds":badIds}, "success")

@maturita_bp.route("/maturita/add/file", methods = ["POST"])
@flask_login.login_required
def add_file():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 103010, {"message": "No permission for that"}, "error")
    
    allMaturitas = 0
    goodMaturitas = 0
    badMaturitas = []

    maturitas = request.files.get("jsonFile", None)

    if not maturitas:
        return send_response(400, 103020, {"message": "File is missing"}, "error")
    
    if len(maturitas.filename.rsplit(".", 1)) < 2 or maturitas.filename.rsplit(".", 1)[1].lower() != "json":
        return send_response(400, 103030, {"message": "Wrong file format"}, "error")
    
    response = check_file_size(4*1024*1024, maturitas.tell())

    if response:
        return response
    
    file_content = maturitas.read().decode("utf-8").strip()

    if not file_content:
        return send_response(400, 103040, {"message": "File is empty"}, "error")

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError:
        return send_response(400, 103050, {"message": "Invalid JSON format"}, "error")
    
    for maturitaData in data.get("maturitas", []):
        grade = maturitaData.get("grade", None)
        maxPoints = maturitaData.get("maxPoints", None)
        startDate = maturitaData.get("startDate", None)
        endDate = maturitaData.get("endDate", None)
        evaluators = maturitaData.get("evaluators", None)

        if not grade or not maxPoints or not startDate or not endDate:
            maturitaResponse, status = send_response(400, 103060, {"message": "Nothing entered", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue

        grade = str(grade)

        if len(grade) > 9 or Maturita.query.filter_by(grade = grade).first():
            maturitaResponse, status = send_response(400, 103070, {"message": "grade too long or already in use", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue

        try:
            maxPoints = float(maxPoints)
        except:
            maturitaResponse, status = send_response(400, 103080, {"message": "maxPoints not float", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue

        if maxPoints > max_FLOAT or maxPoints <= 0:
            maturitaResponse, status = send_response(400, 103090, {"message": "maxPoints not valid", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue

        try:
            endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
        except:
            maturitaResponse, status = send_response(400, 103100, {"message": "End date not integer or is too far", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue

        try:
            startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
        except:
            maturitaResponse, status = send_response(400, 103110, {"message": "startDate not integer or is too far", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue

        if endDate <= startDate:
            maturitaResponse, status = send_response(400, 103120, {"message": "Ending before begining", "maturitaNumber":allMaturitas}, "error")
            badMaturitas.append(maturitaResponse)
            continue
        
        newMaturita = Maturita(grade = grade, maxPoints = maxPoints, startDate = startDate, endDate = endDate)
        db.session.add(newMaturita)
        db.session.commit()

        goodMaturitas += 1

        if evaluators:
            goodIds = []
            badIds = []
            if not isinstance(evaluators, list):
                evaluators = [evaluators]
            
            for evaluator in evaluators:
                try:
                    evaluator = int(evaluator)
                except:
                    badIds.append(evaluator)
                    continue

                if evaluator > max_INT or evaluator <= 0:
                    badIds.append(evaluator)
                    continue

                user = User.query.filter_by(id = evaluator).first()

                if not user or user.role == Role.Student:
                    badIds.append(evaluator)
                    continue

                db.session.add(Evaluator(idUser = evaluator, idMaturita = newMaturita.id))
                goodIds.append(evaluator)

            db.session.commit()

            if badIds:
                maturitaResponse, status = send_response(400, 103130, {"message": "Wrong evaluators", "maturitaNumber":allMaturitas, "badIds":badIds, "goodIds":goodIds}, "error")
                badMaturitas.append(maturitaResponse)
                continue

    db.session.commit()
    
    if goodMaturitas == 0:
        return send_response (400, 103140, {"message": "No maturitas created", "badMaturitas":badMaturitas}, "error") 
            
    return send_response (201, 103151, {"message": "maturitas created successfuly", "badMaturitas":badMaturitas}, "success")

@maturita_bp.route("/maturita/get/file", methods = ["GET"])
@flask_login.login_required
def get_file():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 108010, {"message": "No permission for that"}, "error")

    maturitas = Maturita.query.all()

    data = {"maturitas":[]}
    
    for maturita in maturitas:
        idEvaluator = []
        evaluators = Evaluator.query.filter_by(idMaturita = maturita.id).all()

        for evaluator in evaluators:
            idEvaluator.append(evaluator.idUser)
        
        data["maturitas"].append({"grade":maturita.grade, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate.timestamp(), "endDate":maturita.endDate.timestamp(), "evaluators":idEvaluator})

    buffer = io.BytesIO()
    buffer.write(json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8"))
    buffer.seek(0)

    return send_file(buffer, as_attachment = True, download_name = "maturitas.json", mimetype = "application/json")

@maturita_bp.route("/maturita/update", methods = ["PUT"])
@flask_login.login_required
def update():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 68010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    grade = data.get("grade", None)
    maxPoints = data.get("maxPoints", None)
    startDate = data.get("startDate", None)
    endDate = data.get("endDate", None)
    evaluators = data.get("evaluators", None)
    idMaturita = data.get("idMaturita", None)
    badIds = []
    goodIds = []


    if not idMaturita:
        return send_response(400, 68020, {"message": "idMaturita missing"}, "error")
    if not grade and not isinstance(evaluators, list) and not startDate and not endDate and not maxPoints:
        return send_response(400, 68030, {"message": "nothing entered to change"}, "error")
    try:
        idMaturita = int(idMaturita)
    except:
        return send_response(400, 68040, {"message": "idMaturita not integer"}, "error")
    
    if idMaturita > max_INT or idMaturita <= 0:
        return send_response(400, 68050, {"message": "idMaturita not valid"}, "error")
    
    maturita = Maturita.query.filter_by(id = idMaturita).first()

    if not maturita:
        return send_response(404, 68060, {"message": "maturita not found"}, "error")
    
    if grade:
        grade = str(grade)
        id = maturita.id

        if len(grade) > 9:
                return send_response(400, 68070, {"message": "grade too long"}, "error")
        if Maturita.query.filter(Maturita.grade == grade).first():
            id = Maturita.query.filter(Maturita.grade == grade).first().id

        if id != maturita.id:
            return send_response(400, 68080, {"message": "grade already in use"}, "error")
        
        maturita.grade = grade
    
    if maxPoints:
        try:
            maxPoints = float(maxPoints)
        except:
            return send_response(400, 68090, {"message":"maxPoints not float"}, "error")
        if maxPoints > max_FLOAT or maxPoints <= 0:
            return send_response(400, 68100, {"message": "maxPoints not valid"}, "error")
        
        maturita.maxPoints = maxPoints
        
    if startDate:
        try:
            startDate = datetime.datetime.fromtimestamp(int(startDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 68110, {"message":"startDate not integer or is too far"}, "error")
        if maturita.endDate.replace(tzinfo = datetime.timezone.utc) <= startDate and not endDate:
            return send_response(400, 68120, {"message":"ending before beginning"}, "error")
        maturita.startDate = startDate
        
    if endDate:
        try:
            endDate = datetime.datetime.fromtimestamp(int(endDate)/1000, tz=datetime.timezone.utc)
        except:
            return send_response(400, 68130, {"message":"End date not integer or is too far"}, "error")
       
        if endDate <= maturita.startDate.replace(tzinfo = datetime.timezone.utc):
            return send_response(400, 68140, {"message":"Ending before beginning"}, "error")
        
        maturita.endDate = endDate
    
    db.session.commit()

    maturitasTasks = Maturita_Task.query.filter_by(idMaturita = idMaturita).all()

    for maturitas in maturitasTasks:
        taskMaturita = Task.query.filter_by(id = maturitas.idTask, guarantor = maturitas.guarantor).first()
        taskMaturita.endDate = maturita.endDate
        taskMaturita.points = maturita.maxPoints

    if isinstance(evaluators, list):
        evaluatoring = Evaluator.query.filter_by(idMaturita = idMaturita).all()
        evaluatorIds = []

        for evaluatored in evaluatoring:
            evaluatorIds.append(evaluatored.idUser)
            db.session.delete(evaluatored)
        db.session.commit()
        
        for evaluator in evaluators:
            try:
                evaluator = int(evaluator)
            except:
                badIds.append(evaluator)
                continue

            if evaluator > max_INT or evaluator <= 0:
                badIds.append(evaluator)
                continue

            user = User.query.filter_by(id = evaluator).first()

            if not user or user.role == Role.Student:
                badIds.append(evaluator)
                continue

            db.session.add(Evaluator(idUser = evaluator, idMaturita = idMaturita))
            goodIds.append(evaluator)

            if evaluator in evaluatorIds:
                evaluatorIds.remove(evaluator)

        for evaluatorId in evaluatorIds:
            maturitaTasks = Maturita_Task.query.filter_by(idMaturita = idMaturita, guarantor = evaluatorId).all()
            
            for maturitaTask in maturitaTasks:

                task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = evaluatorId).first()

                db.session.delete(task)

    db.session.commit()

    return send_response(201, 68151, {"message": "maturita updated successfuly", "goodIds":goodIds, "badIds": badIds}, "success")

@maturita_bp.route("/maturita/get/current", methods = ["GET"])
@flask_login.login_required
def get_current():
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    maturita = Maturita.query.filter((Maturita.endDate > now) & (Maturita.startDate < now)).order_by(Maturita.id.desc()).first()

    if not maturita:
        return send_response(400, 69010, {"message": "no maturita in current time range"}, "error")
    
    evaluators = []
    actualEvaluators = Evaluator.query.filter_by(idMaturita = maturita.id)
    for evaluator in actualEvaluators:
        evaluators.append(evaluator.idUser)

    return send_response(201, 69021, {"message": "maturita found successfuly", "maturita":{"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate, "evaluators":evaluators}}, "success")

@maturita_bp.route("/maturita/get/id", methods = ["GET"])
@flask_login.login_required
def get_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 70010, {"message": "id not entered"}, "error")
    
    try:
        id = int(id)
    except:
        return send_response(400, 70020, {"message": "id not integer"}, "error")
    
    if id > max_INT or id <=0:
        return send_response(400, 70030, {"message": "id not valid"}, "error")

    maturita = Maturita.query.filter_by(id = id).first()

    if not maturita:
        return send_response(400, 70040, {"message": "No maturita found"}, "error")
    
    evaluators = []
    actualEvaluators = Evaluator.query.filter_by(idMaturita = maturita.id)
    for evaluator in actualEvaluators:
        evaluators.append(evaluator.idUser)
    
    return send_response(201, 70051, {"message": "maturita found successfuly", "maturita":{"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate, "evaluators":evaluators}}, "success")

@maturita_bp.route("/maturita/delete", methods = ["delete"])
@flask_login.login_required
def delete():
    data = request.get_json(force=True)
    idMaturita = data.get("id", None)
    badIds = []
    goodIds = []

    if flask_login.current_user.role == Role.Student:
        return send_response(403, 71010, {"message": "No permission for that"}, "error")

    if not idMaturita:
        return send_response(400, 71020, {"message": "id not entered"}, "error")
    
    if not isinstance(idMaturita, list):
        idMaturita = [idMaturita]
    
    for id in idMaturita:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue
        
        if id > max_INT or id <=0:
            badIds.append(id)
            continue

        maturita = Maturita.query.filter_by(id = id).first()

        if not maturita:
            badIds.append(id)
            continue
    
        maturitaTasks = Maturita_Task.query.filter_by(idMaturita = id)

        for maturitaTask in maturitaTasks:
            task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
            team = Team.query.filter_by(idTask = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
            versions = Version_Team.query.filter_by(idTeam = team.idTeam, idTask = team.idTask, guarantor = team.guarantor).all()
            user_teams= User_Team.query.filter_by(idTask = maturitaTask.idTask, guarantor = maturitaTask.guarnator)
            conversations = Conversation.query.filter_by(idTask = maturitaTask.idTask, guarantor = maturitaTask.guarantor)

            for version in versions:
                if version.elaboration:
                    delete_upload_version(version.idTask, version.idTeam, version.elaboration, version.guarantor, version.idVersion)

            if task.task:
                delete_upload_task(task.task, task.guarantor, task.id)
            
            for user_team in user_teams:
                cancel_reminder(user_team.idUser, user_team.idTask, user_team.guarantor)
            
            for conversation in conversations:
                cancel_archive_conversation(conversation.idConversation, conversation.idTask, conversation.guarantor, conversation.idUser1, conversation.idUser2)
            
        db.session.delete(maturita)
        goodIds.append(id)
        db.session.commit()

    if not goodIds:
        return send_response(400, 71030, {"message": "no deletion"}, "error")

    return send_response(201, 71041, {"message": "maturita deleted successfuly", "goodIds":goodIds, "badIds":badIds}, "success")

@maturita_bp.route("/maturita/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    allMaturitas = []

    if not amountForPaging:
        return send_response(400, 72010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 72020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 72030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 72040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 72050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 72060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 72070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 72080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        maturitas = Maturita.query.order_by(Maturita.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Maturita.query.count()
    else:
        maturitas, count = maturita_paging(searchQuery = searchQuery, amountForPaging = amountForPaging, pageNumber = pageNumber)

    for maturita in maturitas:
        evaluators = []
        actualEvaluators = Evaluator.query.filter_by(idMaturita = maturita.id)
        for evaluator in actualEvaluators:
            evaluators.append(evaluator.idUser)
        allMaturitas.append({"grade":maturita.grade, "id":maturita.id, "maxPoints":maturita.maxPoints, "startDate":maturita.startDate, "endDate":maturita.endDate, "evaluators":evaluators})

    return send_response(201, 72091, {"message": "maturita created successfuly", "maturita":allMaturitas, "count":count}, "success")

