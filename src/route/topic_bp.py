import flask_login
from src.models.Maturita_Task import Maturita_Task
from src.models.Task import Task
from src.models.Team import Team
from src.models.Version_Team import Version_Team
from src.models.User_Team import User_Team
from src.models.Topic import Topic
from src.utils.paging import topic_paging
from src.utils.response import send_response
from src.utils.enums import Role, Type
from src.models.Conversation import Conversation
from src.utils.archive_conversation import cancel_archive_conversation
from src.models.User import User
from src.utils.task import delete_upload_task
from src.utils.version import delete_upload_version
from flask import request, Blueprint, send_file
from app import db, max_INT
from src.utils.reminder import cancel_reminder
from src.utils.check_file import check_file_size
import json
import io

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

@topic_bp.route("/topic/add/file", methods = ["POST"])
@flask_login.login_required
def add_file():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 102010, {"message": "No permission for that"}, "error")
    
    allTopics = 0
    goodTopics = 0
    badTopics = []

    topics = request.files.get("jsonFile", None)

    if not topics:
        return send_response(400, 102020, {"message": "File is missing"}, "error")
    
    if len(topics.filename.rsplit(".", 1)) < 2 or topics.filename.rsplit(".", 1)[1].lower() != "json":
        return send_response(400, 102030, {"message": "Wrong file format"}, "error")
    
    response = check_file_size(4*1024*1024, topics.tell())

    if response:
        return response
    
    file_content = topics.read().decode("utf-8").strip()

    if not file_content:
        return send_response(400, 102040, {"message": "File is empty"}, "error")

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError:
        return send_response(400, 102050, {"message": "Invalid JSON format"}, "error")
    
    for topicData in data.get("topics") or []:

        if not isinstance(topicData, dict):
            continue

        allTopics += 1

        name = topicData.get("name", None)

        if not name:
            topicResponse, status = send_response(400, 102060, {"topicNumber": allTopics, "message":"Name not entered"}, "error")
            badTopics.append(topicResponse)
            continue
        
        name = str(name)
        
        if len(name)>255 or Topic.query.filter_by(name = name).first():
            topicResponse, status = send_response(400, 102070, {"topicNumber": allTopics, "message":"Name too long or name in use"}, "error")
            badTopics.append(topicResponse)
            continue

        newTopic = Topic(name=name)
        db.session.add(newTopic)

        goodTopics += 1

    db.session.commit()
    
    if goodTopics == 0:
        return send_response(400, 102080, {"message": "No topics created", "badTopics":badTopics}, "error") 
            
    return send_response(201, 102091, {"message": "Topics created successfuly", "badTopics":badTopics}, "success")

@topic_bp.route("/topic/get/file", methods = ["GET"])
@flask_login.login_required
def get_file():
    if flask_login.current_user.role == Role.Student:
        return send_response(403, 107010, {"message": "No permission for that"}, "error")

    topics = Topic.query.all()

    data = {"topics":[]}
    
    for topic in topics:
        
        data["topics"].append({"name":topic.name})

    buffer = io.BytesIO()
    buffer.write(json.dumps(data, indent=4, ensure_ascii=False).encode("utf-8"))
    buffer.seek(0)

    return send_file(buffer, as_attachment = True, download_name = "topics.json", mimetype = "application/json")

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
                    cancel_reminder(userTeam.idUser, userTeam.idTask, userTeam.guarantor)

                for version in versions:
                    if version.elaboration:
                        delete_upload_version(version.idTask, version.idTeam, version.elaboration, version.guarantor, version.idVersion)

            if task.type == Type.Maturita:
                conversations = Conversation.query.filter_by(idTask = task.idTask, guarantor = task.guarantor)

                for conversation in conversations:
                    if conversation.idUser1 == conversation.guarantor:
                        user = User.query.filter_by(id = conversation.idUser2).first()
                    else:
                        user = User.query.filter_by(id = conversation.idUser1).first()

                    if user.role != Role.Student:
                        continue

                    cancel_archive_conversation(conversation.idConversation, conversation.idTask, conversation.guarnator, conversation.idUser1, conversation.idUser2)

            if task.task:
                delete_upload_task(task.task, task.guarantor, task.id)

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
