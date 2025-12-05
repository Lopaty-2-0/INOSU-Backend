from flask import Blueprint, request
from src.models.Version_Team import Version_Team
from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Task import Task
from src.utils.response import send_response
from src.utils.enums import Status
from src.utils.versions import make_version, version_save, version_delete
import flask_login
import datetime
from app import db
from src.utils.check_file import check_file_size

version_team = Blueprint("version_team", __name__)
elaboration_extensions = ["pdf", "docx", "odt", "html", "zip"]
maxINT = 4294967295

@version_team.route("/version_team/add", methods = ["PUT"])
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

    team = Team.query.filter_by(idTask = idTask, idTeam = idTeam).first()
    
    if not team:
        return send_response(400, 38070, {"message": "This team doesnt exist"}, "error")
    if not User_Team.query.filter_by(idUser = flask_login.current_user.id, idTeam = idTeam, idTask = idTask).first() or team.status != Status.Approved:
        return send_response(400, 38080, {"message": "User doesnt have rights"}, "error")
    if not elaboration:
        return send_response(400, 38090, {"message": "Elaboration not entered"}, "error")
    if not elaboration.filename.rsplit(".", 1)[1].lower() in elaboration_extensions:
        return send_response(400, 38100, {"message": "Wrong file format"}, "error")
    if len(elaboration.filename) > 255:
        return send_response(400, 38110, {"message": "File name too long"}, "error")
    if Task.query.filter_by(id = idTask).first().deadline < datetime.datetime.now():
        return send_response(400, 38120, {"message": "Cannot update version after deadline"}, "error")
    
    id = await make_version(idTask = idTask, idTeam = idTeam)
    status = await version_save(idTeam = idTeam, idTask = idTask, idVersion = id, file = elaboration)

    if not status:
        return send_response(400, 38130, {"message": "File already exists"}, "error")
    
    new_version = Version_Team(idTeam = idTeam, idTask = idTask, elaboration = elaboration.filename, idVersion = id)
    db.session.add(new_version)
    db.session.commit()

    return send_response(400, 38141, {"message": "Version_team created"}, "success")

@version_team.route("/version_team/change", methods = ["POST"])
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
    if Task.query.filter_by(id = idTask).first().deadline < datetime.datetime.now():
        return send_response(400, 49130, {"message": "Cannot update version after deadline"}, "error")
    
    await version_delete(idTeam = idTeam, idTask = idTask, idVersion = idVersion, fileName = version.elaboration)

    version.elaboration = None
    db.session.commit()

    return send_response(400, 49141, {"message": "Version_team updated"}, "success")
