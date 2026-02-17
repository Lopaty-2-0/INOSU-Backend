from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from app import db
from src.utils.version import delete_upload_version
from src.utils.reminder import cancel_reminder

def make_team(idTask, status, name, isTeam, guarantor):
    if not Team.query.filter_by(idTask = idTask, guarantor = guarantor).first():
        id = 1
    else:
        id = Team.query.filter_by(idTask=idTask, guarantor = guarantor).order_by(Team.idTeam.desc()).first().idTeam + 1
    
    newTeam = Team(idTeam = id, idTask = idTask, review = None, status = status, name = name, points = None, isTeam = isTeam, guarantor = guarantor)
    db.session.add(newTeam)
    db.session.commit()

    return id

def delete_teams_for_task(idTask, guarantor):
    teams = Team.query.filter_by(idTask = idTask, guarantor = guarantor)

    for team in teams:
        users = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam, guarantor = guarantor)
        versions = Version_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam, guarantor = guarantor)

        for version in versions:
            if version.elaboration:
                delete_upload_version(version.idTask, version.idTeam, version.elaboration, version.guarantor, version.idVersion)

        for user in users:
            cancel_reminder(user.idUser, idTask, guarantor)