from src.models.Version_Team import Version_Team
from app import db, task_path, ssh
from src.utils.sftp_utils import sftp_createDir_async, sftp_stat_async, sftp_removeDir_async, sftp_put_async, sftp_remove_async
import os
from src.utils.team import team_createDir

async def make_version(idTask, idTeam, file, guarantor):
    if not Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = guarantor).first():
        id = 1
    else:
        id = Version_Team.query.filter_by(idTask=idTask, idTeam = idTeam, guarantor = guarantor).order_by(Version_Team.idVersion.desc()).first().idVersion + 1

    status = await version_save(idTeam, idTask, id, file, guarantor = guarantor)

    if status:
        newVersion = Version_Team(idVersion = id, idTask = idTask, elaboration = file.filename, idTeam = idTeam, guarantor = guarantor)
        
        db.session.add(newVersion)
        db.session.commit()

    return status

async def delete_versions_for_team(idTask, idTeam, guarantor):
    versions = Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = guarantor)

    for version in versions:
        db.session.delete(version)
        await version_deleteDir(idTeam, idTask, version.idVersion, guarantor)
        
    db.session.commit()

async def version_deleteDir(idTeam, idTask, idVersion, guarantor):
    filePath = task_path + str(guarantor) + "/" +  str(idTask) + "/" + str(idTeam) + "/" + str(idVersion)
    if not await sftp_stat_async(ssh, filePath):
        return False
    
    await sftp_removeDir_async(ssh, filePath)

    return True

async def version_createDir(idTeam, idTask, idVersion, guarantor):
    filePath = task_path + str(guarantor) + "/" +  str(idTask) + "/" + str(idTeam) + "/" + str(idVersion)

    if await sftp_stat_async(ssh, filePath):
        return False
    
    try:
        await sftp_createDir_async(ssh, filePath)
    except:
        await team_createDir(idTeam = idTeam, idTask = idTask, guarantor = guarantor)
        await version_createDir(idTeam, idTask, idVersion, guarantor)

    return True

async def version_save(idTeam, idTask, idVersion, file, guarantor):
    fileName = file.filename
    filePath = task_path + str(guarantor) + "/" +  str(idTask) + "/" + str(idTeam) + "/" + str(idVersion)

    await version_createDir(idTeam, idTask, idVersion, guarantor)

    if await sftp_stat_async(ssh, filePath + "/" + fileName):
        return False 
        
    file.save("files/" + fileName)
    await sftp_put_async(ssh, "files/" + fileName, filePath + "/" + fileName)
    os.remove("files/" + fileName)

    return True

async def version_delete(idTeam, idTask, idVersion, fileName, guarantor):
    filePath = task_path + str(guarantor) + "/" + str(idTask) + "/" + str(idTeam) + "/" + str(idVersion) + "/" + fileName

    if not await sftp_stat_async(ssh, filePath):
        return False 

    await sftp_remove_async(ssh = ssh, filePath = filePath)

    return True