from flask import Blueprint, request
from src.models.Version_Team import Version_Team
from src.models.Team import Team
from src.models.User_Team import User_Team
from src.utils.response import send_response
from src.utils.enums import Status
from src.utils.versions import make_version, version_save, version_delete
import flask_login
from app import db
from src.utils.check_file import check_file_size

version_team = Blueprint("version_team", __name__)
elaboration_extensions = ["pdf", "docx", "odt", "html", "zip"]

@version_team.route("/version_team/add", methods = ["PUT"])
@check_file_size(2 * 1024 * 1024)
@flask_login.login_required
async def add():
    elaboration = request.files.get("elaboration", None)
    idTask = request.form.get("guarantor", None)
    idTeam = request.form.get("idTeam", None)

    team = Team.query.filter_by(idTask = idTask, idTeam = idTeam).first()

    if not team:
        return send_response(400, 38010, {"message": "This team doesnt exist"}, "error")
    if not User_Team.query.filter_by(idUser = flask_login.current_user.id, idTeam = idTeam, idTask = idTask).first() or team.status != Status.Approved:
        return send_response(400, 38020, {"message": "User doesnt have rights"}, "error")
    if not elaboration:
        return send_response(400, 38030, {"message": "Elaboration not entered"}, "error")
    if not elaboration.filename.rsplit(".", 1)[1].lower() in elaboration_extensions:
        return send_response(400, 38040, {"message": "Wrong file format"}, "error")
    if len(elaboration.filename) > 255:
        return send_response(400, 38050, {"message": "File name too long"}, "error")
    
    id = await make_version(idTask = idTask, idTeam = idTeam)
    status = await version_save(idTeam = idTeam, idTask = idTask, idVersion = id, file = elaboration)

    if not status:
        return send_response(400, 38060, {"message": "File already exists"}, "error")
    
    new_version = Version_Team(idTeam = idTeam, idTask = idTask, elaboration = elaboration.filename, idVersion = id)
    db.session.add(new_version)
    db.session.commit()

    return send_response(400, 38071, {"message": "Version_team created"}, "success")

@version_team.route("/version_team/change", methods = ["POST"])
@flask_login.login_required
async def change():
    data = request.get_json(force = True)
    idTask = data.get("guarantor", None)
    idTeam = data.get("idTeam", None)
    idVersion = data.get("idVersion", None)

    team = Team.query.filter_by(idTask = idTask, idTeam = idTeam).first()
    version = Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, idVersion = idVersion).first()

    if not team:
        return send_response(400, 49010, {"message": "This team doesnt exist"}, "error")
    if not version:
        return send_response(400, 49020, {"message": "This version doesnt exist"}, "error")
    if not User_Team.query.filter_by(idUser = flask_login.current_user.id, idTeam = idTeam, idTask = idTask).first() or team.status != Status.Approved:
        return send_response(400, 49030, {"message": "User doesnt have rights"}, "error")
    
    await version_delete(idTeam = idTeam, idTask = idTask, idVersion = idVersion, fileName = version.elaboration)

    version.elaboration = None
    db.session.commit()

    return send_response(400, 49041, {"message": "Version_team updated"}, "success")
