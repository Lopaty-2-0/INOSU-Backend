from src.models.Team import Team
from src.models.User_Team import User_Team
from src.utils.task import team_createDir
from app import db, task_path

async def make_team(idTask, status):
    if not Team.query.filter_by(idTask = idTask).first():
        id = 1
    else:
        id = Team.query.filter_by(idTask=idTask).order_by(Team.idTeam.desc()).first().idTeam + 1
    
    new_team = Team(idTeam = id, idTask = idTask, elaboration = None, review = None, status = status)
    await team_createDir(task_path, id, idTask)
    db.session.add(new_team)
    db.session.commit()

    return id

def delete_teams_for_task(idTask):
    teams = Team.query.filter_by(idTask = idTask)

    for team in teams:
        users = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam)

        for user in users:
            db.session.delete(user)

        db.session.delete(team)
        
    db.session.commit()