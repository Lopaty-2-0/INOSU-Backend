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
maxINT = 4294967295
maxFLOAT = 34.0e+38

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
    if idTask > maxINT or idTask <=0:
        return send_response(400, 30030, {"message": "idTask not valid"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 30040, {"message": "Nonexistent task"}, "error")
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 30050, {"message": "User is not guarantor"}, "error")
    if len(name) > 255:
        return send_response(400, 30060, {"message": "Name too long"}, "error")
    if Team.query.filter_by(idTask = idTask, name = name).first():
        return send_response(400, 30070, {"message": "Team with this name already exists"}, "error")
    
    await make_team(idTask = idTask, status = Status.Approved, name = name)
    
    return send_response(201, 30081, {"message": "Team created successfuly"}, "success")

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
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 31030, {"message": "idTask not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 31040, {"message": "idTask not valid"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 31050, {"message": "idTeam not integer"}, "error")
    if idTeam > maxINT or idTeam <=0:
        return send_response(400, 31060, {"message": "idTeam not valid"}, "error")
    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 31070, {"message": "Nonexistent task"}, "error")
    if not Team.query.filter_by(idTeam = idTeam, idTask = idTask).first():
        return send_response(400, 31080, {"message": "Nonexistent team"}, "error")
    if Task.query.filter_by(id = idTask).first().guarantor != flask_login.current_user.id:
        return send_response(400, 31090, {"message": "User is not guarantor"}, "error")
    
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

    return send_response(200, 31101, {"message": "team deleted successfuly"}, "success")

@team_bp.route("/team/update", methods=["PUT"])
@flask_login.login_required
async def update():
    data = request.get_json(force = True)
    idTask = data.get("idTask", None)
    idTeam = data.get("idTeam", None)
    status = data.get("status", None)
    review = data.get("review", None)
    points = data.get("points", None)

    if not idTask:
        return send_response(400, 32010, {"message": "IdTask not entered"}, "error")
    if not idTeam:
        return send_response(400, 32020, {"message": "IdTeam not entered"}, "error")
    try:
        idTask = int(idTask)
    except:
        return send_response(400, 31030, {"message": "idTask not integer"}, "error")
    if idTask > maxINT or idTask <=0:
        return send_response(400, 31040, {"message": "idTask not valid"}, "error")
    try:
        idTeam = int(idTeam)
    except:
        return send_response(400, 31050, {"message": "idTeam not integer"}, "error")
    if idTeam > maxINT or idTeam <=0:
        return send_response(400, 31060, {"message": "idTeam not valid"}, "error")
    
    task = Task.query.filter_by(id = idTask).first()

    if not task:
        return send_response(400, 32030, {"message": "Nonexistent task"}, "error")
    
    team = Team.query.filter_by(idTeam = idTeam, idTask = idTask).first()

    if not team:
        return send_response(400, 32040, {"message": "Nonexistent team"}, "error")
    if not flask_login.current_user.id == task.guarantor:
        return send_response(400, 32050, {"message": "User doesnt have rights"}, "error")
    if not review and not status and not points and status != Status.Pending.value:
        return send_response(400, 32060, {"message": "Nothing entered to change"}, "error")
    if status:
        if status not in [s.value for s in Status]:
            return send_response(400, 32070, {"message": "Status not our type"}, "error")
        elif status != Status.Pending.value:
            team.status = Status(status)
    if points:
        try:
            points = float(points)
        except:
            return send_response(400, 32080, {"message": "Points are not integer or float"}, "error")
        if points > maxFLOAT or points <= 0:
            return send_response(400, 32090, {"message": "Points not valid"}, "error")
        if points > task.points:
            return send_response(400, 32100, {"message": "Can not give more points tha task has"}, "error")
        team.points = points
    if review:
        if len(review) > 65535:
            return send_response(400, 32100, {"message": "Review too long"}, "error")
        team.review = review
    
    db.session.commit()

    return send_response(200, 32111, {"message": "team updated"}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 41040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 41050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 41060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
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
    if idTask > maxINT or idTask <=0:
        return send_response(400, 41110, {"message": "idTask not valid"}, "error")

    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 41120, {"message": "Nonexistent task"}, "error")
    
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

    return send_response(200, 41131, {"message": "All teams for this task", "users":users, "count": count}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 56040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 56050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 56060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
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
    if idTask > maxINT or idTask <=0:
        return send_response(400, 56110, {"message": "IdTask not valid"}, "error")

    if not Task.query.filter_by(id = idTask).first():
        return send_response(400, 56120, {"message": "Nonexistent task"}, "error")
    
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

    return send_response(200, 56131, {"message": "All teams for this task", "teams":right_teams, "count": count}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 40040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 40050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 40060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 40070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 40080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 40090, {"message": "Status not our type"}, "error")
    
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
    
    return send_response(200, 40101, {"message": "All guarantor tasks with these statuses for current user", "teams":right_teams, "count": count}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 57040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 57050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 57060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 57070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 57080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 57090, {"message": "Status not our type"}, "error")
    
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
    
    return send_response(200, 57101, {"message": "All guarantor tasks with these statuses for current user", "users":users, "count": count}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 44040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 44050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 44060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 44070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 44080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 44090, {"message": "Status not our type"}, "error")
    
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
                
    return send_response(200, 44101, {"message": "All teams for this task and statuses", "teams": right_teams, "count":count}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 58040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 58050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 58060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
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
    if idTask > maxINT or idTask <=0:
        return send_response(400, 58110, {"message": "IdTask not valid"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 58120, {"message": "Status not our type"}, "error")
    
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

    return send_response(200, 58131, {"message": "All teams for this task and statuses", "users":users, "count":count}, "success")

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
    
    if amountForPaging > maxINT:
        return send_response(400, 53040, {"message": "amountForPaging too big"}, "error")
    
    if not pageNumber:
        return send_response(400, 53050, {"message": "pageNumber not entered"}, "error")
    
    try:
        pageNumber = int(pageNumber)
    except:
        return send_response(400, 53060, {"message": "pageNumber not integer"}, "error")
    if pageNumber > maxINT + 1:
        return send_response(400, 53070, {"message": "pageNumber too big"}, "error")
    
    pageNumber -= 1

    if pageNumber < 0:
        return send_response(400, 53080, {"message": "pageNumber must be bigger than 0"}, "error")
    
    if status not in [stat.value for stat in Status]:
        return send_response(400, 53090, {"message": "Status not our type"}, "error")
    
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
                
    return send_response(200, 53101, {"message": "All tasks with these statuses for current user", "users":users, "teams":right_teams, "count":count}, "success")