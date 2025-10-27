from src.models.Team import Team
from src.models.User_Team import User_Team
from src.utils.sftp_utils import sftp_stat_async, sftp_removeDir_async, sftp_createDir_async
from app import db, task_path, ssh

async def make_team(idTask, status, name):
    if not Team.query.filter_by(idTask = idTask).first():
        id = 1
    else:
        id = Team.query.filter_by(idTask=idTask).order_by(Team.idTeam.desc()).first().idTeam + 1
    
    new_team = Team(idTeam = id, idTask = idTask, elaboration = None, review = None, status = status, name = name)
    await team_createDir(task_path, id, idTask)
    db.session.add(new_team)
    db.session.commit()

    return id

async def delete_teams_for_task(idTask):
    teams = Team.query.filter_by(idTask = idTask)

    for team in teams:
        users = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam)

        for user in users:
            db.session.delete(user)

        db.session.delete(team)
        await team_delete(team.idTeam, idTask)
        
    db.session.commit()

async def team_delete(idTeam, idTask):
    file_path = task_path + str(idTask) + "/" + str(idTeam)
    if not await sftp_stat_async(ssh, file_path):
        return False
    
    await sftp_removeDir_async(ssh, file_path)

    return True

async def team_createDir(idTeam, idTask):
    file_path = task_path + str(idTask) + "/" + str(idTeam)

    if await sftp_stat_async(ssh, file_path):
            return False
    
    await sftp_createDir_async(ssh, file_path)

    return True    