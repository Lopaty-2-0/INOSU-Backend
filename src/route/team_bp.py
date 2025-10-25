"""
Tento soubor je uložen čistě z důvodu, aby se vědělo, které rescodes mohou být znovu použity
"""

#rescode 380000

from flask import request, Blueprint
import flask_login
from app import db, task_path
from src.models.Team import Team
from src.models.User import User
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.utils.task import team_delete
from src.utils.response import send_response
from src.utils.team import make_team
from src.utils.enums import Status
from src.utils.task import team_delete, task_save_sftp, task_delete_sftp

team_bp = Blueprint("team", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@team_bp.route("/team/add", methods=["POST"])
@flask_login.login_required
async def add():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)

    if not idTask:
        return send_response(400, 30010, {"message": "IdTask not entered"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 30020, {"message": "Nonexistent task"}, "error")
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 30030, {"message": "User is not guarant"}, "error")
    
    await make_team(idTask = idTask, status = Status.Approved)
    
    return send_response(201, 30041, {"message": "Team created successfuly"}, "success")

@team_bp.route("/team/delete", methods=["DELETE"])
@flask_login.login_required
async def delete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)

    if not idTask:
        return send_response(400, 31010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 31020, {"message": "IdTeam not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 31030, {"message": "Nonexistent task"}, "error")
    if not Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        return send_response(400, 31040, {"message": "Nonexistent team"}, "error")
    if Task.query.filter_by(id = idTask).first().guarantor != flask_login.current_user.id:
        return send_response(400, 31050, {"message": "User is not guarantor"}, "error")
    
    users = User_Team.query.filter_by(idTask = idTask, idTeam = idTeam)
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask).first()

    for user in user:
        db.session.delete(user)

    await team_delete(task_path = task_path, idTeam = idTeam, idTask = idTask)
    db.session.delete(team)
    db.session.commit()

    return send_response(200, 31061, {"message": "team deleted successfuly"}, "success")

@team_bp.route("/team/update", methods=["PUT"])
@flask_login.login_required
async def update():
    idTask = request.form.get("idTask", None)
    idTeam = request.form.get("idTeam", None)
    status = request.form.get("status", None)
    review = request.files.get("review", None)
    elaboration = request.files.get("elaboration", None)
    ids = []

    if not idTask:
        return send_response(400, 32010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 32020, {"message": "IdTeam not entered"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 32030, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask).first()

    if not team:
        return send_response(400, 32040, {"message": "Nonexistent team"}, "error")
    
    
    if flask_login.current_user.id == task.guarantor:
        if not review and status not in [s.value for s in Status] and status != Status.Pending.value:
            return send_response(400, 32050, {"message": "Nothing not entered to change"}, "error")
        if review:
            if not review.filename.rsplit(".", 1)[1].lower() in task_extensions:
                return send_response(400, 32060, {"message": "Wrong file format"}, "error")
            if not team.status == Status.Approved.value:
                return send_response(400, 32070, {"message": "Can not do that"}, "error")
            if len(review.filename) > 255:
                return send_response(400, 32080, {"message": "File name too long"}, "error")
            if team.review:
                await task_delete_sftp(task_path + str(task.id) + "/", str(idTeam) + "/review")

            filename = await task_save_sftp(task_path + str(task.id) + "/", review, str(idTeam) + "/review")
            team.review = filename
        else:
            if team.review:
                await task_delete_sftp(task_path + str(task.id) + "/", str(idTeam) + "/review")
            team.review = None

        if status:
            team.status = Status(status)
    else:
        users = User_Team.query.filter_by(idTeam = idTeam, idTask = idTask)
        for user in users:
            ids.append(user.id)
        
        if not flask_login.current_user.id in ids:
            return send_response(400, 32090, {"message": "User doesnt have rights"}, "error")
        
        if team.status != Status.Approved:
            return send_response(400, 32100, {"message": "WUser doesnt have rights"}, "error")
        elif elaboration:
            if not elaboration.filename.rsplit(".", 1)[1].lower() in task_extensions:
                return send_response(400, 32110, {"message": "Wrong file format"}, "error")
            if len(elaboration.filename) > 255:
                return send_response(400, 32120, {"message": "File name too long"}, "error")
            if team.elaboration:
                await task_delete_sftp(task_path + str(task.id) + "/", idTeam + "/elaboration")

            filename = await task_save_sftp(task_path + str(task.id) + "/", elaboration, idTeam + "/elaboration")
            team.elaboration = filename
        else :
            if team.elaboration:
                await task_delete_sftp(task_path + str(task.id) + "/", idTeam + "/elaboration")
            team.elaboration = None
        
    return send_response(200, 32131, {"message": "team updated"}, "success")

@team_bp.route("/team/get", methods=["GET"])
@flask_login.login_required
def get_by_task():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    teams = []
    users = []

    if not idTask:
        return send_response(400, 41010, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 41020, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTask = idTask)

    for t in team:
        count = User_Team.query.filter_by(idTask=idTask, idTeam=t.idTeam).count()
        
        if count == 1:
            user = User.query.filter_by(id = User_Team.query.filter_by(idTask = idTask, idTeam = t.idTeam).first().idUser).first()
            users.append({
                        "idTeam":t.idTeam,
                        "userData":{
                            "id":user.id,
                            "name":user.name,
                            "surname":user.surname,
                            "profilePicture":user.profilePicture
                        }
                        })

        teams.append({
                    "status":t.status.value,
                    "elaboration":t.elaboration,
                    "review":t.review, 
                    "idTeam":t.idTeam,
                    "count": count
                    })

    return send_response(200, 41031, {"message": "All teams for this task", "teams":teams, "users":users}, "success")
        