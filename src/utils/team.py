from src.models.Team import Team
from src.models.User_Team import User_Team
from src.models.Version_Team import Version_Team
from src.utils.sftp_utils import sftp_stat_async, sftp_removeDir_async, sftp_createDir_async
from app import db, task_path, ssh
from src.utils.task import task_createDir

async def make_team(idTask, status, name, isTeam, guarantor):
    if not Team.query.filter_by(idTask = idTask, guarantor = guarantor).first():
        id = 1
    else:
        id = Team.query.filter_by(idTask=idTask, guarantor = guarantor).order_by(Team.idTeam.desc()).first().idTeam + 1
    
    newTeam = Team(idTeam = id, idTask = idTask, review = None, status = status, name = name, points = None, isTeam = isTeam, guarantor = guarantor)
    await team_createDir(id, idTask, guarantor)
    db.session.add(newTeam)
    db.session.commit()

    return id

async def delete_teams_for_task(idTask, guarantor):
    teams = Team.query.filter_by(idTask = idTask, guarantor = guarantor)

    for team in teams:
        users = User_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam, guarantor = guarantor)
        versions = Version_Team.query.filter_by(idTask = idTask, idTeam = team.idTeam, guarantor = guarantor)

        for version in versions:
            db.session.delete(version)

        for user in users:
            db.session.delete(user)

        db.session.commit()
        db.session.delete(team)
        await team_deleteDir(team.idTeam, idTask, guarantor)
        
    db.session.commit()

async def team_deleteDir(idTeam, idTask, guarantor):
    filePath = task_path  + str(guarantor) + "/" + str(idTask) + "/" + str(idTeam)
    if not await sftp_stat_async(ssh, filePath):
        return False
    
    await sftp_removeDir_async(ssh, filePath)

    return True

async def team_createDir(idTeam, idTask, guarantor):
    filePath = task_path + str(guarantor) + "/" + str(idTask) + "/" + str(idTeam)

    if await sftp_stat_async(ssh, filePath):
            return False
    
    try:
        await sftp_createDir_async(ssh, filePath)
    except:
        await task_createDir(id = idTask, guarantor = guarantor)
        await team_createDir(idTeam, idTask, guarantor)

    return True    