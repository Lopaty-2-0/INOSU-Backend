from flask import Blueprint, request
from src.models.Version_Team import Version_Team
from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.utils.response import send_response
from src.utils.enums import Status
from src.utils.version import make_version, version_delete
import flask_login
from app import db, maxINT
from src.utils.check_file import check_file_size
import datetime

version_team_bp = Blueprint("version_team", __name__)
elaboration_extensions = ["pdf", "docx", "odt", "html", "zip"]

@version_team_bp.route("/version_team/add", methods = ["POST"])
@check_file_size(2 * 1024 * 1024)
@flask_login.login_required
async def add():
    elaboration = request.files.get("elaboration", None)
    idTask = request.form.get("idTask", None)
    idTeam = request.form.get("idTeam", None)

    if not idTeam:
        return send_response(400, 38010, {"message": "idTeam not entered"}, "error")
    if not idTask:
        return send_response(400, 38020, {"message": "idTask not entered"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 38030, {"message": "idTeam not integer"}, "error")
    if idTeam > maxINT or idTeam <=0:
        return send_response(400, 38040, {"message": "idTeam not valid"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 38050, {"message": "idTask not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 38060, {"message": "idTask not valid"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 38070, {"message": "This task doesnt exist"}, "error")
    
    team = Team.query.filter_by(idTask = idTask, idTeam = idTeam).first()
    
    if not team:
        return send_response(400, 38080, {"message": "This team doesnt exist"}, "error")
    if not User_Team.query.filter_by(idUser = flask_login.current_user.id, idTeam = idTeam, idTask = idTask).first() or team.status != Status.Approved:
        return send_response(400, 38090, {"message": "User doesnt have rights"}, "error")
    if not elaboration:
        return send_response(400, 38100, {"message": "Elaboration not entered"}, "error")
    if not elaboration.filename.rsplit(".", 1)[1].lower() in elaboration_extensions:
        return send_response(400, 38110, {"message": "Wrong file format"}, "error")
    if len(elaboration.filename) > 255:
        return send_response(400, 38120, {"message": "File name too long"}, "error")
    if task.deadline:
        if  task.deadline< datetime.datetime.now(datetime.timezone.utc):
            return send_response(400, 38130, {"message": "Cannot update version after deadline"}, "error")
    
    status = await make_version(idTask = idTask, idTeam = idTeam, file = elaboration)

    if not status:
        return send_response(400, 38140, {"message": "File already exists"}, "error")
    
    return send_response(200, 38151, {"message": "Version_team created"}, "success")

@version_team_bp.route("/version_team/change", methods = ["PUT"])
@flask_login.login_required
async def change():
    data = request.get_json(force = True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)
    idVersion = data.get("idVersion", None)
    
    if not idTeam:
        return send_response(400, 49010, {"message": "idTeam not entered"}, "error")
    if not idTask:
        return send_response(400, 49020, {"message": "idTask not entered"}, "error")
    if not idVersion:
        return send_response(400, 49030, {"message": "idVersion not entered"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 49040, {"message": "idTeam not integer"}, "error")
    if idTeam > maxINT or idTeam <=0:
        return send_response(400, 49050, {"message": "idTeam not valid"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 49060, {"message": "idTask not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 49070, {"message": "idTask not valid"}, "error")
    try:
        idVersion = int(idVersion)
    except:
        return send_response(400, 49080, {"message": "idVersion not integer"}, "error")
    if idVersion > maxINT or idVersion <=0:
        return send_response(400, 49090, {"message": "idVersion not valid"}, "error")

    team = Team.query.filter_by(idTask = idTask, idTeam = idTeam).first()
    version = Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, idVersion = idVersion).first()

    if not team:
        return send_response(400, 49100, {"message": "This team doesnt exist"}, "error")
    if not version:
        return send_response(400, 49110, {"message": "This version doesnt exist"}, "error")
    if not User_Team.query.filter_by(idUser = flask_login.current_user.id, idTeam = idTeam, idTask = idTask).first() or team.status != Status.Approved:
        return send_response(400, 49120, {"message": "User doesnt have rights"}, "error")
    if Task.query.filter_by(id = idTask).first().deadline < datetime.datetime.now(datetime.timezone.utc):
        return send_response(400, 49130, {"message": "Cannot update version after deadline"}, "error")
    
    if version.elaboration:
        await version_delete(idTeam = idTeam, idTask = idTask, idVersion = idVersion, fileName = version.elaboration)

        version.elaboration = None
    db.session.commit()

    return send_response(200, 49141, {"message": "Version_team updated"}, "success")

@version_team_bp.route("/version_team/get", methods = ["GET"])
@flask_login.login_required
def get():
    idTask = request.args.get("idTask", None)
    idTeam = request.args.get("idTeam", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    versions = []

    if not amountForPaging:
        return send_response(400, 59010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 59020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 59030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > maxINT:
        return send_response(400, 59040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 59050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 59060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 59070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 59080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idTask:
        return send_response(400, 59090, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 59100, {"message": "idTask not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 59110, {"message": "idTask not valid"}, "error")
    
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 59120, {"message": "Nonexistent task"}, "error")
    
    if not idTeam:
        return send_response(400, 59130, {"message": "idTask not entered"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 59140, {"message": "idTask not integer"}, "error")
    if idTeam > maxINT or idTeam <=0:
        return send_response(400, 59150, {"message": "idTask not valid"}, "error")
    
    if not Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        return send_response(400, 59160, {"message": "Nonexistent team"}, "error")
    
    versions_team = Version_Team.query.filter(Version_Team.idTask == idTask, Version_Team.idTeam == idTeam).order_by(Version_Team.idVersion.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
    count = Version_Team.query.filter(Version_Team.idTask == idTask, Version_Team.idTeam == idTeam).count()

    for version in versions_team:
        versions.append({"idVersion":version.idVersion, "elaboration":version.elaboration, "createdAt":version.createdAt})

    return send_response(200, 59171, {"message": "All versions for this team", "versions":versions, "count": count}, "success")