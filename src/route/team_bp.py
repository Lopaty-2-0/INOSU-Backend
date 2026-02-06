from flask import request, Blueprint
import flask_login
from app import db, max_FLOAT, max_INT
from src.models.Team import Team
from src.models.User import User
from src.models.Task import Task
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from src.utils.team import team_deleteDir, make_team
from src.utils.response import send_response
from src.utils.enums import Status, Type
from src.utils.paging import team_paging
from sqlalchemy import or_
from src.utils.all_user_classes import all_user_classes
from src.utils.reminder import cancel_reminder
from src.utils.maturita_task import maturita_task_delete
from src.models.Maturita import Maturita
import datetime

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
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 30020, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 30030, {"message": "idTask not valid"}, "error")
    
    task = Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).first()

    if task.type == Type.Maturita:
        return send_response(400, 30040, {"message": "Cannot add team to this task"}, "error")

    if not task:
        return send_response(400, 30050, {"message": "Nonexistent task"}, "error")
    if name:
        name = str(name)
        if len(name) > 255:
            return send_response(400, 30060, {"message": "Name too long"}, "error")
        if Team.query.filter_by(idTask = idTask,  name = name, guarantor = flask_login.current_user.id).first():
            return send_response(400, 30070, {"message": "Team with this name already exists"}, "error")
    
    await make_team(idTask = idTask, status = Status.Approved, name = name, isTeam = True, guarantor = flask_login.current_user.id)
    
    return send_response(201, 30081, {"message": "Team created successfuly"}, "success")

@team_bp.route("/team/delete", methods=["DELETE"])
@flask_login.login_required
async def delete():
    data = request.get_json(force=True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)
    badIds = []
    goodIds = []

    if not idTask:
        return send_response(400, 31010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 31020, {"message": "IdTeam not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 31030, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 31040, {"message": "idTask not valid"}, "error")
    if not Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).first():
        return send_response(400, 31050, {"message": "Nonexistent task"}, "error")
    if not isinstance(idTeam, list):
        idTeam = [idTeam]

    for id in idTeam:
        try:
            id = int(id)
        except:
            badIds.append(id)
            continue
        if id > max_INT or id <=0:
            badIds.append(id)
            continue

        if not Team.query.filter_by(idTeam = id, idTask = idTask).first():
            badIds.append(id)
            continue

        users = User_Team.query.filter_by(idTask = idTask, idTeam = id, guarantor = flask_login.current_user.id)
        team = Team.query.filter_by(idTeam = id, idTask = idTask, guarantor = flask_login.current_user.id).first()
        versions = Version_Team.query.filter_by(idTeam = id, idTask = idTask, guarantor = flask_login.current_user.id)

        for user in users:
            db.session.delete(user)

            cancel_reminder(idUser = user.idUser, idTask = idTask, guarantor = flask_login.current_user.id)
             
        for version in versions:
            db.session.delete(version)
        
        db.session.commit()

        await team_deleteDir(idTeam = id, idTask = idTask, guarantor = flask_login.current_user.id)
        db.session.delete(team)
        goodIds.append(id)

    db.session.commit()

    return send_response(200, 31071, {"message": "teams deleted successfuly", "badIds": badIds, "goodIds": goodIds}, "success")

@team_bp.route("/team/update", methods=["PUT"])
@flask_login.login_required
async def update():
    data = request.get_json(force = True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)
    status = data.get("status", None)
    review = data.get("review", None)
    points = data.get("points", None)
    name = data.get("name", None)

    if not idTask:
        return send_response(400, 32010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 32020, {"message": "IdTeam not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 32030, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 32040, {"message": "idTask not valid"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 32050, {"message": "idTeam not integer"}, "error")
    if idTeam > max_INT or idTeam <=0:
        return send_response(400, 32060, {"message": "idTeam not valid"}, "error")
    
    task = Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).first()

    if not task:
        return send_response(400, 32070, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask, guarantor = flask_login.current_user.id).first()

    if not team:
        return send_response(400, 32080, {"message": "Nonexistent team"}, "error")
    if status and Task.query.filter_by(id = idTask, guarantor = flask_login.current_user.id).type == Type.Maturita:
        if status not in [s.value for s in Status]:
            return send_response(400, 32090, {"message": "Status not our type"}, "error")
        elif status != Status.Pending.value:
            user = User_Team.query.filter_by(idTeam = team.idTeam, idTask = idTask, guarantor = flask_login.current_user.id).first()
            if user:
                now = datetime.datetime.now(tz=datetime.timezone.utc)
                maturita = Maturita.query.filter(Maturita.startDate <= now, Maturita.endDate >= now)
                if maturita:
                    await maturita_task_delete(user.idUser, maturita.id)
            team.status = Status(status)
    if points or points == 0:
        try:
            points = float(points)
        except:
            return send_response(400, 32100, {"message": "Points are not integer or float"}, "error")
        if points > max_FLOAT or points < 0:
            return send_response(400, 32110, {"message": "Points not valid"}, "error")
        if points > task.points:
            return send_response(400, 32120, {"message": "Can not give more points tha task has"}, "error")
        team.points = points
    if isinstance(review, str):
        review = str(review)
        if len(review) > 65535:
            return send_response(400, 32130, {"message": "Review too long"}, "error")
        team.review = review
        team.reviewUpdatedAt = datetime.datetime.now(datetime.timezone.utc)
    if isinstance(name, str):
        if len(name) > 255:
            return send_response(400, 32140, {"message": "Name too long"}, "error")
        team.name = name
        team.teamUpdatedAt = datetime.datetime.now(datetime.timezone.utc)

    db.session.commit()

    return send_response(200, 32151, {"message": "team updated"}, "success")

@flask_login.login_required
@team_bp.route("/team/get/users", methods=["GET"])
def get_users_task():
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    users = []

    if not amountForPaging:
        return send_response(400, 41010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 41020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 41030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 41040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 41050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 41060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 41070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 41080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idTask:
        return send_response(400, 41090, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 41100, {"message": "idTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 41110, {"message": "idTask not valid"}, "error")

    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 41120, {"message": "Nonexistent task"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == False).order_by(Team.idTeam.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == False).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, typeOfTeam="users", guarantor = flask_login.current_user.id)
    
    for team in teams:
        user = User.query.filter_by(id = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).first().idUser).first()
        version = Version_Team.query.filter_by(idTask=idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt
        
        users.append({
                    "idTeam":team.idTeam,
                    "name":team.name,
                    "status":team.status.value,
                    "elaboration":elaboration,
                    "createdAt":createdAt,
                    "review":team.review, 
                    "points":team.points,
                    "isTeam": team.isTeam,
                    "teamUpdatedAt":team.teamUpdatedAt,
                    "reviewUpdatedAt":team.reviewUpdatedAt,
                    "userData":{
                        "id": user.id,
                        "name": user.name,
                        "surname": user.surname,
                        "abbreviation": user.abbreviation,
                        "role": user.role.value,
                        "profilePicture": user.profilePicture,
                        "email": user.email,
                        "idClass": all_user_classes(user.id),
                        "createdAt":user.createdAt,
                        "updatedAt": user.updatedAt
                    }
                    })

    return send_response(200, 41131, {"message": "All teams for this task", "users":users, "count": count}, "success")

@flask_login.login_required
@team_bp.route("/team/get/teams", methods=["GET"])
def get_teams_task():
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    rightTeams = []


    if not amountForPaging:
        return send_response(400, 56010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 56020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 56030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 56040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 56050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 56060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 56070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 56080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if not idTask:
        return send_response(400, 56090, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 56100, {"message": "IdTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 56110, {"message": "IdTask not valid"}, "error")

    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 56120, {"message": "Nonexistent task"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == True).order_by(Team.idTeam.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == True).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, guarantor = flask_login.current_user.id)
    
    for team in teams:
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam, guarantor = flask_login.current_user.id).count()
        version = Version_Team.query.filter_by(idTask=idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt
        
        rightTeams.append({
                    "idTeam":team.idTeam,
                    "count": counts,
                    "name":team.name,
                    "status":team.status.value,
                    "elaboration":elaboration,
                    "teamUpdatedAt":team.teamUpdatedAt,
                    "createdAt":createdAt,
                    "review":team.review, 
                    "points":team.points,
                    "isTeam": team.isTeam,
                    "reviewUpdatedAt":team.reviewUpdatedAt
                    })

    return send_response(200, 56131, {"message": "All teams for this task", "teams":rightTeams, "count": count}, "success")

@team_bp.route("/team/get/teams/status/guarantor", methods=["GET"])
@flask_login.login_required
def get_teams_with_status_and_guarantor():
    status = request.args.get("status", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    rightTeams = []

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
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 40090, {"message": "Status not our type"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.guarantor == flask_login.current_user.id, Team.status == Status(status)).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == True).order_by(Team.idTeam.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.guarantor == flask_login.current_user.id, Team.status == Status(status)).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == True).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", guarantor=flask_login.current_user.id)

    for team in teams:
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam, guarantor = flask_login.current_user.id).count()
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt

        rightTeams.append({
                    "status":team.status.value,
                    "review":team.review, 
                    "idTeam":team.idTeam,
                    "count": counts,
                    "name":team.name,
                    "teamUpdatedAt":team.teamUpdatedAt,
                    "isTeam": team.isTeam,
                    "reviewUpdatedAt":team.reviewUpdatedAt,
                    "points":team.points,
                    "createdAt":createdAt,
                    "elaboration": elaboration
                    })
    
    return send_response(200, 40101, {"message": "All guarantor tasks with these statuses for current user", "teams":rightTeams, "count": count}, "success")

@team_bp.route("/team/get/users/status/guarantor", methods=["GET"])
@flask_login.login_required
def get_users_with_status_and_guarantor():
    status = request.args.get("status", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    users = []

    
    if not amountForPaging:
        return send_response(400, 57010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 57020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 57030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 57040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 57050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 57060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 57070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 57080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 57090, {"message": "Status not our type"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.guarantor == flask_login.current_user.id, Team.status == Status(status)).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == False).order_by(Team.idTeam.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.guarantor == flask_login.current_user.id, Team.status == Status(status)).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == False).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", guarantor=flask_login.current_user.id, typeOfTeam="users")

    for team in teams:

        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt

        user = User.query.filter_by(id = User_Team.query.filter_by(idTask = team.idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).first().idUser).first()
        users.append({
                    "idTeam":team.idTeam,
                    "name":team.name,
                    "status":team.status.value,
                    "review":team.review, 
                    "points":team.points,
                    "isTeam": team.isTeam,
                    "teamUpdatedAt":team.teamUpdatedAt,
                    "createdAt":createdAt,
                    "reviewUpdatedAt":team.reviewUpdatedAt,
                    "userData":{
                        "id":user.id,
                        "name":user.name,
                        "surname":user.surname,
                        "profilePicture":user.profilePicture
                    },
                    "elaboration": elaboration
                    })
    
    return send_response(200, 57101, {"message": "All guarantor tasks with these statuses for current user", "users":users, "count": count}, "success")

@team_bp.route("/team/get/teams/status/idTask", methods=["GET"])
@flask_login.login_required
def get_teams_with_status_and_idTask():
    status = request.args.get("status", None)
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    rightTeams = []

    if not amountForPaging:
        return send_response(400, 44010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 44020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 44030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 44040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 44050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 44060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 44070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 44080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 44090, {"message": "Status not our type"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status), Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == True).order_by(Team.idTeam.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status), Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == True).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=idTask, typeOfIds = "task", guarantor=flask_login.current_user.id)
    
    for team in teams:
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam, guarantor = flask_login.current_user.id).count()
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt

        rightTeams.append({
                    "status":team.status.value,
                    "review":team.review, 
                    "idTeam":team.idTeam,
                    "count": counts,
                    "name":team.name,
                    "points":team.points,
                    "createdAt":createdAt,
                    "isTeam": team.isTeam,
                    "teamUpdatedAt":team.teamUpdatedAt,
                    "reviewUpdatedAt":team.reviewUpdatedAt,
                    "elaboration": elaboration
                    })
                
    return send_response(200, 44101, {"message": "All teams for this task and statuses", "teams": rightTeams, "count":count}, "success")

@team_bp.route("/team/get/users/status/idTask", methods=["GET"])
@flask_login.login_required
def get_users_with_status_and_idTask():
    status = request.args.get("status", None)
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    users = []

    if not amountForPaging:
        return send_response(400, 58010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 58020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 58030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 58040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 58050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 58060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 58070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 58080, {"message": "pageNumber must be bigger than 0"}, "error")
    if not idTask:
        return send_response(400, 58090, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 58100, {"message": "IdTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 58110, {"message": "IdTask not valid"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 58120, {"message": "Status not our type"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status), Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == False).order_by(Team.idTeam.desc()).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status),Team.guarantor == flask_login.current_user.id).group_by(Team.idTeam, Team.idTask).having(Team.isTeam == False).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=idTask, typeOfIds = "task", typeOfTeam="users", guarantor = flask_login.current_user.id)
    
    for team in teams:
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt
        
        user = User.query.filter_by(id = User_Team.query.filter_by(idTask = team.idTask, idTeam = team.idTeam, guarantor = flask_login.current_user.id).first().idUser).first()
        users.append({
                    "idTeam":team.idTeam,
                    "name":team.name,
                    "status":team.status.value,
                    "review":team.review, 
                    "points":team.points,
                    "isTeam": team.isTeam,
                    "createdAt":createdAt,
                    "reviewUpdatedAt":team.reviewUpdatedAt,
                    "teamUpdatedAt":team.teamUpdatedAt,
                    "userData":{
                        "id":user.id,
                        "name":user.name,
                        "surname":user.surname,
                        "profilePicture":user.profilePicture
                    },
                    "elaboration": elaboration
                    })

    return send_response(200, 58131, {"message": "All teams for this task and statuses", "users":users, "count":count}, "success")

@team_bp.route("/team/get/status/elaboration", methods=["GET"])
@flask_login.login_required
def get_by_status_elaboration(): 
    status = request.args.get("status", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    users = []
    rightTeams = []
    pairs = []
    
    if not amountForPaging:
        return send_response(400, 53010, {"message": "amountForPaging not entered"}, "error")

    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 53020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 53030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if amountForPaging > max_INT:
        return send_response(400, 53040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 53050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 53060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > max_INT + 1:
        return send_response(400, 53070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 53080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 53090, {"message": "Status not our type"}, "error")
    
    userTeams = User_Team.query.filter_by(idUser = flask_login.current_user.id)

    for userTeam in userTeams:
        pairs.append((userTeam.idTeam, userTeam.idTask, userTeam.guarantor))

    if pairs:
        conditions = [
            (Team.idTeam == teamId) & (Team.idTask == taskId) & (Team.guarantor == guarantor)
            for teamId, taskId, guarantor in pairs
            ]
        
        if not searchQuery:
            teams = Team.query.filter(or_(*conditions), Team.status == Status(status)).offset(amountForPaging * pageNumber).limit(amountForPaging)
            count = Team.query.filter(or_(*conditions), Team.status == Status(status)).count()
        else:
            teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=conditions, typeOfIds = "elaboration")
    else:
        count = 0
        teams = []
    
    for team in teams:
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam, guarantor = team.guarantor).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
            createdAt = None
        else:
            elaboration = version.elaboration
            createdAt = version.createdAt
        
        if team.isTeam:
            user = flask_login.current_user
            users.append({
                        "idTeam":team.idTeam,
                        "name":team.name,
                        "status":team.status.value,
                        "review":team.review, 
                        "points":team.points,
                        "isTeam": team.isTeam,
                        "createdAt":createdAt,
                        "reviewUpdatedAt":team.reviewUpdatedAt,
                        "teamUpdatedAt":team.teamUpdatedAt,
                        "userData":{
                            "id":user.id,
                            "name":user.name,
                            "surname":user.surname,
                            "profilePicture":user.profilePicture
                        },
                        "elaboration": elaboration
                        })
        else:
            rightTeams.append({
                        "status":team.status.value,
                        "review":team.review, 
                        "idTeam":team.idTeam,
                        "createdAt":createdAt,
                        "count": User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam, guarantor = team.guarantor).count(),
                        "name":team.name,
                        "points":team.points,
                        "isTeam": team.isTeam,
                        "teamUpdatedAt":team.teamUpdatedAt,
                        "reviewUpdatedAt":team.reviewUpdatedAt,
                        "elaboration": elaboration
                        })
                
    return send_response(200, 53101, {"message": "All tasks with these statuses for current user", "users":users, "teams":rightTeams, "count":count}, "success")

@team_bp.route("/team/get/info")
@flask_login.login_required
def get_team_info():
    idTeam = request.args.get("idTeam", None)
    idTask = request.args.get("idTask", None)
    guarantor = request.args.get("guarantor", None)
    users = []

    if not idTeam:
        return send_response(400, 45010, {"message": "idTeam not entered"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 45020, {"message": "IdTask not integer"}, "error")
    if idTeam > max_INT or idTeam <=0:
        return send_response(400, 45030, {"message": "IdTask not valid"}, "error")
    
    if not guarantor:
        return send_response(400, 45040, {"message": "guarantor not entered"}, "error")
    try:
        guarantor = int(guarantor)
    except:
        return send_response(400, 45050, {"message": "guarantor not integer"}, "error")
    if guarantor > max_INT or guarantor <=0:
        return send_response(400, 45060, {"message": "guarantor not valid"}, "error")
    
    user = User.query.filter_by(id = guarantor).first()

    if not user:
        return send_response(400, 45070, {"message": "Nonexistent guarantor"}, "error")
    
    if not idTask:
        return send_response(400, 45080, {"message": "idTask not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 45090, {"message": "IdTask not integer"}, "error")
    if idTask > max_INT or idTask <=0:
        return send_response(400, 45100, {"message": "IdTask not valid"}, "error")
    
    task = Task.query.filter_by(id = idTask, guarantor = guarantor).first()

    if not task:
        return send_response(400, 45110, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = guarantor).first()

    if not team:
        return send_response(400, 45120, {"message": "Nonexistent team"}, "error")

    userTeams = User_Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = guarantor).order_by(User_Team.idUser.desc())

    for user in userTeams:
        users.append(user.idUser)
    
    teamInfo = {"idTeam": idTeam, "idTask": idTask, "name": team.name, "points":team.points, "review":team.review, "status":team.status.value, "isTeam": team.isTeam, "reviewUpdatedAt":team.reviewUpdatedAt, "teamUpdatedAt":team.teamUpdatedAt}
    
    return send_response(200, 45091, {"message": "Team info found", "users":users, "team":teamInfo}, "success")