from flask import request, Blueprint
import flask_login
from app import db
from src.models.Team import Team
from src.models.User import User
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from src.utils.team import team_delete
from src.utils.response import send_response
from src.utils.team import make_team
from src.utils.enums import Status

team_bp = Blueprint("team", __name__)
task_extensions = ["pdf", "docx", "odt", "html", "zip"]

@team_bp.route("/team/add", methods=["POST"])
@flask_login.login_required
async def add():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    name = data.get("name", None)

    if not idTask:
        return send_response(400, 30010, {"message": "IdTask not entered"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 30020, {"message": "Nonexistent task"}, "error")
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 30030, {"message": "User is not guarant"}, "error")
    
    await make_team(idTask = idTask, status = Status.Approve, name = name)
    
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
    versions = Version_Team.query.filter_by(idTeam = idTeam, idTask = idTask)

    for user in users:
        db.session.delete(user)
    
    for version in versions:
        db.session.delete(version)

    await team_delete(idTeam = idTeam, idTask = idTask)
    db.session.delete(team)
    db.session.commit()

    return send_response(200, 31061, {"message": "team deleted successfuly"}, "success")

@team_bp.route("/team/update", methods=["PUT"])
@flask_login.login_required
async def update():
    #TODO: předělat na to, že review není soubor
    data = request.get_json(force = True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)
    status = data.get("status", None)
    review = data.get("review", None)
    points = data.get("points", None)
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
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 32050, {"message": "User doesnt have rights"}, "error")
    if not review and not status and not points and status != Status.Pending.value:
        return send_response(400, 32060, {"message": "Nothing not entered to change"}, "error")
    if status not in [s.value for s in Status]:
        return send_response(400, 32070, {"message": "Status not our type"}, "error")
    else:
        team.status = Status(status)
    if isinstance(points, int):
        points = float(points)
    if not isinstance(points, float):
        return send_response(400, 32080, {"message": "Points are not integer or float"}, "error")
    
    team.review = review
    
    db.session.commit()

    return send_response(200, 32091, {"message": "team updated"}, "success")

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
    
    teams = Team.query.filter_by(idTask = idTask)

    for team in teams:
        count = User_Team.query.filter_by(idTask=idTask, idTeam=team.idTeam).count()
        
        if count == 1:
            user = User.query.filter_by(id = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam).first().idUser).first()
            users.append({
                        "idTeam":team.idTeam,
                        "name":team.name,
                        "userData":{
                            "id":user.id,
                            "name":user.name,
                            "surname":user.surname,
                            "profilePicture":user.profilePicture
                        }
                        })

        teams.append({
                    "status":team.status.value,
                    "elaboration":team.elaboration,
                    "review":team.review, 
                    "idTeam":team.idTeam,
                    "count": count,
                    "name":team.name,
                    "points":team.points
                    })

    return send_response(200, 41031, {"message": "All teams for this task", "teams":teams, "users":users}, "success")
        