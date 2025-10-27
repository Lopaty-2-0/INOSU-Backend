from src.models.Version_Team import Version_Team
from src.models.Team import Team
from app import db, task_path, ssh
from src.utils.sftp_utils import sftp_createDir_async, sftp_stat_async, sftp_removeDir_async, sftp_put_async, sftp_remove_async
import os

async def make_version(idTask, idTeam):
    if not Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam).first():
        id = 1
    else:
        id = Version_Team.query.filter_by(idTask=idTask, idTeam = idTeam).order_by(Version_Team.idVersion.desc()).first().idVersion_Team + 1

    new_version = Version_Team(idVersion = id, idTask = idTask, elaboration = None, idTeam = idTeam)
    await version_createDir(task_path, id, idTask)
    db.session.add(new_version)
    db.session.commit()

    return id

async def delete_versions_for_team(idTask, idTeam):
    versions = Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam)

    for version in versions:
        db.session.delete(version)
        await version_deleteDir(idTeam, idTask, version.idVersion)
        
    db.session.commit()

async def version_deleteDir(idTeam, idTask, idVersion):
    file_path = task_path + str(idTask) + "/" + str(idTeam) + "/" + str(idVersion)
    if not await sftp_stat_async(ssh, file_path):
        return False
    
    await sftp_removeDir_async(ssh, file_path)

    return True

async def version_createDir(idTeam, idTask, idVersion):
    file_path = task_path + str(idTask) + "/" + str(idTeam) + "/" + str(idVersion)

    if await sftp_stat_async(ssh, file_path):
        return False
    
    await sftp_createDir_async(ssh, file_path)

    return True

async def version_save(idTeam, idTask, idVersion, file):
    fileName = file.filename
    file_path = task_path + str(idTask) + "/" + str(idTeam) + "/" + str(idVersion) + fileName

    if await sftp_stat_async(ssh, file_path):
        return False 
    else:
        ssh.open_sftp().mkdir(file_path)
        
    file.save("files/" + fileName)
    await sftp_put_async(ssh, "files/" + fileName, file_path)
    os.remove("files/" + fileName)

    return True

async def version_delete(idTeam, idTask, idVersion, fileName):
    file_path = task_path + str(idTask) + "/" + str(idTeam) + "/" + str(idVersion) + fileName

    if not await sftp_stat_async(ssh, file_path):
        return False 

    sftp_remove_async(ssh = ssh, file_path = file_path)

    return True
