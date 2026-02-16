import flask_login
from src.models.Maturita_Task import Maturita_Task
from src.models.Task import Task
from src.models.Team import Team
from src.models.Version_Team import Version_Team
from src.models.User_Team import User_Team
from src.models.Topic import Topic
from src.utils.paging import topic_paging
from src.utils.response import send_response
from src.utils.enums import Role
from src.utils.task import delete_upload_task
from src.utils.version import delete_upload_version
from flask import request, Blueprint
from app import db, max_INT


topic_bp = Blueprint("topic", __name__)

@topic_bp.route("/topic/add", methods = ["POST"])
@flask_login.login_required
def add():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 63010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    name = data.get("name", None)

    if not name:
        return send_response(400, 63020, {"message": "name missing"}, "error")
    
    name = str(name)

    if len(name) > 255:
            return send_response(400, 63030, {"message": "Name too long"}, "error")
    if Topic.query.filter_by(name = name).first():
        return send_response(400, 63040, {"message": "name already in use"}, "error")
    
    newtopic = Topic(name = name)
    db.session.add(newtopic)
    db.session.commit()

    return send_response (201, 63051, {"message": "topic created successfuly", "topic":{"name":newtopic.name, "id":newtopic.id}}, "success")

@topic_bp.route("/topic/delete", methods = ["DELETE"])
@flask_login.login_required
def delete():
    badIds = []
    goodIds = []
    
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 64010, {"message": "No permission for that"}, "error")
    
    data = request.get_json(force=True)
    idTopic = data.get("id", None)

    if not idTopic:
        return send_response(400, 64020, {"message": "Id is missing"}, "error")
    if not isinstance(idTopic, list):
        idTopic = [idTopic]
    
    for id in idTopic:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue

        if id > max_INT or id <= 0:
            badIds.append(id)
            continue

        if not Topic.query.filter_by(id = id).first() :
            badIds.append(id)
            continue

        maturitaTasks = Maturita_Task.query.filter_by(idTopic = id)

        for maturitaTask in maturitaTasks:
            task = Task.query.filter_by(id = maturitaTask.idTask, guarantor = maturitaTask.guarantor).first()
            teams = Team.query.filter_by(idTask = maturitaTask.idTask, guarantor = maturitaTask.guarantor)

            for team in teams:
                userTeams = User_Team.query.filter_by(idTask = maturitaTask.idTask, guarantor = maturitaTask.guarantor, idTeam = team.idTeam)
                versions = Version_Team.query.filter_by(idTask = maturitaTask.idTask, guarantor = maturitaTask.guarantor, idTeam = team.idTeam)
                
                for userTeam in userTeams:
                    db.session.delete(userTeam)
                for version in versions:
                    if version.elaboration:
                        delete_upload_version(version.idTask, version.idTeam, version.elaboration, version.guarantor, version.idVersion)
                    db.session.delete(version)
                
                db.session.commit()
                db.session.delete(team)
            
            db.session.delete(maturitaTask)

            db.session.commit()
            delete_upload_task(task.task, task.guarantor, task.id)
            db.session.delete(task)

        db.session.commit()
        db.session.delete(Topic.query.filter_by(id = id).first())
        goodIds.append(id)

    db.session.commit()
    
    if not goodIds:
        return send_response (400, 64030, {"message": "No deletion"}, "error")
    
    return send_response (200, 64041, {"message": "topics deleted successfuly", "goodIds":goodIds, "badIds":badIds}, "success")

@topic_bp.route("/topic/get", methods = ["GET"])
@flask_login.login_required
def get():
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)

    topics = []

    if not amountForPaging:
        return send_response(400, 65010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 65020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 65030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 65040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 65050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 65060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 65070, {"message": "amountForPaging too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 65080, {"message": "pageNumber must be bigger than 0"}, "error")

    if not searchQuery:
        topic = Topic.query.order_by(Topic.id.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Topic.query.count()
    else:
        topic, count = topic_paging(amountForPaging = amountForPaging, pageNumber = pageNumber, searchQuery = searchQuery)

    for s in topic:
        topics.append({"id":s.id,"name":s.name})

    return send_response (200, 65091, {"message": "topics found", "topics":topics, "count":count}, "success")

@topic_bp.route("/topic/get/id", methods=["GET"])
@flask_login.login_required
def get_by_id():
    id = request.args.get("id", None)

    if not id:
        return send_response(400, 66010, {"message": "Id not entered"}, "error")
    try:
        id = int(id)
    except:
        return send_response(400, 66020, {"message": "Id not integer"}, "error")
    if id > max_INT or id <=0:
        return send_response(400, 66030, {"message": "Id not valid"}, "error")

    topic = Topic.query.filter_by(id=id).first()
    
    if not topic:
        return send_response(404, 66040, {"message": "topic not found"}, "error")

    return send_response(200, 66051, {"message": "topic found", "topic": {"id":topic.id,"name":topic.name}}, "success")
