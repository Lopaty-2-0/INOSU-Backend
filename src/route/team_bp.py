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
from src.utils.paging import team_paging
from sqlalchemy import or_, func
from src.utils.all_user_classes import all_user_classes

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
        return send_response(400, 30030, {"message": "User is not guarantor"}, "error")
    if Team.query.filter_by(idTask = idTask, name = name).first():
        return send_response(400, 30030, {"message": "Team with this name already exists"}, "error")
    
    await make_team(idTask = idTask, status = Status.Approved, name = name)
    
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
    elif status != Status.Pending.value:
        team.status = Status(status)
    try:
        points = float(points)
    except:
        return send_response(400, 32080, {"message": "Points are not integer or float"}, "error")
    
    team.review = review
    
    db.session.commit()

    return send_response(200, 32091, {"message": "team updated"}, "success")

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
    
    if not pageNumber:
        return send_response(400, 41040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 41050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 41060, {"message": "pageNumber must be bigger than 0"}, "error")

    if not idTask:
        return send_response(400, 41070, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 41080, {"message": "Nonexistent task"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, typeOfTeam="users")
    
    for team in teams:
        user = User.query.filter_by(id = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam).first().idUser).first()
        version = Version_Team.query.filter_by(idTask=idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration
        
        users.append({
                    "idTeam":team.idTeam,
                    "name":team.name,
                    "status":team.status.value,
                    "elaboration":elaboration,
                    "review":team.review, 
                    "points":team.points,
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

    return send_response(200, 41091, {"message": "All teams for this task", "users":users, "count": count}, "success")

@flask_login.login_required
@team_bp.route("/team/get/teams", methods=["GET"])
def get_teams_task():
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    right_teams = []


    if not amountForPaging:
        return send_response(400, 56010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 56020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 56030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 56040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 56050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 56060, {"message": "pageNumber must be bigger than 0"}, "error")

    if not idTask:
        return send_response(400, 56070, {"message": "idTask not entered"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 56080, {"message": "Nonexistent task"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging)
    
    for team in teams:
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam).count()
        version = Version_Team.query.filter_by(idTask=idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration
        
        right_teams.append({
                    "idTeam":team.idTeam,
                    "count": counts,
                    "name":team.name,
                    "status":team.status.value,
                    "elaboration":elaboration,
                    "review":team.review, 
                    "points":team.points,
                    })

    return send_response(200, 56091, {"message": "All teams for this task", "teams":right_teams, "count": count}, "success")

@team_bp.route("/team/get/teams/status/guarantor", methods=["GET"])
@flask_login.login_required
def get_teams_with_status_and_guarantor():
    status = request.args.get("status", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    right_teams = []
    guarantorIds = []
    
    if not amountForPaging:
        return send_response(400, 40010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 40020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 40030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 40040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 40050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 40060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 40070, {"message": "Status not our type"}, "error")
    
    tasks = Task.query.filter_by(guarantor = flask_login.current_user.id)

    for task in tasks:
        guarantorIds.append(task.id)
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask.in_(guarantorIds), Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask.in_(guarantorIds), Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=guarantorIds)

    for team in teams:
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam).count()
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration

        right_teams.append({
                    "status":team.status.value,
                    "review":team.review, 
                    "idTeam":team.idTeam,
                    "count": counts,
                    "name":team.name,
                    "points":team.points,
                    "elaboration": elaboration
                    })
    
    return send_response(200, 40081, {"message": "All guarantor tasks with these statuses for current user", "teams":right_teams, "count": count}, "success")

@team_bp.route("/team/get/users/status/guarantor", methods=["GET"])
@flask_login.login_required
def get_users_with_status_and_guarantor():
    status = request.args.get("status", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    users = []
    guarantorIds = []
    
    if not amountForPaging:
        return send_response(400, 57010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 57020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 57030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 57040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 57050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 57060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 57070, {"message": "Status not our type"}, "error")
    
    tasks = Task.query.filter_by(guarantor = flask_login.current_user.id)

    for task in tasks:
        guarantorIds.append(task.id)
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask.in_(guarantorIds), Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask.in_(guarantorIds), Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=guarantorIds, typeOfTeam="users")

    for team in teams:

        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration

        user = User.query.filter_by(id = User_Team.query.filter_by(idTask = team.idTask, idTeam = team.idTeam).first().idUser).first()
        users.append({
                    "idTeam":team.idTeam,
                    "name":team.name,
                    "status":team.status.value,
                    "review":team.review, 
                    "points":team.points,
                    "userData":{
                        "id":user.id,
                        "name":user.name,
                        "surname":user.surname,
                        "profilePicture":user.profilePicture
                    },
                    "elaboration": elaboration
                    })
    
    return send_response(200, 57081, {"message": "All guarantor tasks with these statuses for current user", "users":users, "count": count}, "success")

@team_bp.route("/team/get/teams/status/idTask", methods=["GET"])
@flask_login.login_required
def get_teams_with_status_and_idTask():
    status = request.args.get("status", None)
    idTask = request.args.get("idTask", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    right_teams = []

    if not amountForPaging:
        return send_response(400, 44010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 44020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 44030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 44040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 44050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 44060, {"message": "Status not our type"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) != 1).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=idTask, typeOfIds = "task")
    
    for team in teams:
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam).count()
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration

        right_teams.append({
                    "status":team.status.value,
                    "review":team.review, 
                    "idTeam":team.idTeam,
                    "count": counts,
                    "name":team.name,
                    "points":team.points,
                    "elaboration": elaboration
                    })
                
    return send_response(200, 44071, {"message": "All teams for this task and statuses", "teams": right_teams, "count":count}, "success")

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
    
    if not pageNumber:
        return send_response(400, 58040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 58050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 58060, {"message": "Status not our type"}, "error")
    
    if not searchQuery:
        teams = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).offset(amountForPaging * pageNumber).limit(amountForPaging)
        count = Team.query.outerjoin(User_Team, Team.idTeam == User_Team.idTeam).filter(Team.idTask == idTask, Team.status == Status(status)).group_by(Team.idTeam).having(func.count(User_Team.idUser) == 1).count()
    else:
        teams, count = team_paging(searchQuery = searchQuery, pageNumber = pageNumber, amountForPaging = amountForPaging, specialSearch = Status(status), typeOfSpecialSearch="status", ids=idTask, typeOfIds = "task", typeOfTeam="users")
    
    for team in teams:
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration
        
        user = User.query.filter_by(id = User_Team.query.filter_by(idTask = team.idTask, idTeam = team.idTeam).first().idUser).first()
        users.append({
                    "idTeam":team.idTeam,
                    "name":team.name,
                    "status":team.status.value,
                    "review":team.review, 
                    "points":team.points,
                    "userData":{
                        "id":user.id,
                        "name":user.name,
                        "surname":user.surname,
                        "profilePicture":user.profilePicture
                    },
                    "elaboration": elaboration
                    })

    return send_response(200, 58071, {"message": "All teams for this task and statuses", "users":users, "count":count}, "success")

@team_bp.route("/team/get/status/elaboration", methods=["GET"])
@flask_login.login_required
def get_by_status_elaboration(): 
    status = request.args.get("status", None)
    amountForPaging = request.args.get("amountForPaging", None)
    pageNumber = request.args.get("pageNumber", None)
    searchQuery = request.args.get("searchQuery", None)
    users = []
    right_teams = []
    pairs = []
    
    if not amountForPaging:
        return send_response(400, 53010, {"message": "amountForPaging not entered"}, "error")
    
    try:
        amountForPaging = int(amountForPaging)
    except:
        return send_response(400, 53020, {"message": "amountForPaging not integer"}, "error")
    
    if amountForPaging < 1:
        return send_response(400, 53030, {"message": "amountForPaging smaller than 1"}, "error")
    
    if not pageNumber:
        return send_response(400, 53040, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 53050, {"message": "pageNumber not integer"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 53060, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 53070, {"message": "Status not our type"}, "error")
    
    user_teams = User_Team.query.filter_by(idUser = flask_login.current_user.id)

    for user_team in user_teams:
        pairs.append((user_team.idTeam, user_team.idTask))


    if pairs:
        conditions = [
            (Team.idTeam == team_id) & (Team.idTask == task_id)
            for team_id, task_id in pairs
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
        counts = User_Team.query.filter_by(idTask=team.idTask, idTeam=team.idTeam).count()
        version = Version_Team.query.filter_by(idTask=team.idTask, idTeam = team.idTeam).order_by(Version_Team.idVersion.desc()).first()

        if not version:
            elaboration = None
        else:
            elaboration = version.elaboration
        
        if counts == 1:
            user = flask_login.current_user
            users.append({
                        "idTeam":team.idTeam,
                        "name":team.name,
                        "status":team.status.value,
                        "review":team.review, 
                        "points":team.points,
                        "userData":{
                            "id":user.id,
                            "name":user.name,
                            "surname":user.surname,
                            "profilePicture":user.profilePicture
                        },
                        "elaboration": elaboration
                        })
        else:
            right_teams.append({
                        "status":team.status.value,
                        "review":team.review, 
                        "idTeam":team.idTeam,
                        "count": counts,
                        "name":team.name,
                        "points":team.points,
                        "elaboration": elaboration
                        })
                
    return send_response(200, 53081, {"message": "All tasks with these statuses for current user", "users":users, "teams":right_teams, "count":count}, "success")