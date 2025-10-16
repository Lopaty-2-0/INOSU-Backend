import os
import asyncio
from src.utils.sftp_utils import sftp_put_async, sftp_stat_async, sftp_removeDir_async, sftp_remove_async
from app import ssh

async def task_save_sftp(file_path, file, id):
    state = True

    if not await sftp_stat_async(ssh, file_path):
        ssh.open_sftp().mkdir(file_path)

    file_path = file_path + str(id)

    if not await sftp_stat_async(ssh, file_path):
        ssh.open_sftp().mkdir(file_path)

    fileName = file.filename
    filePath = file_path + "/" + fileName

    if await sftp_stat_async(ssh, filePath):
        await sftp_remove_async(ssh, file_path)
        
    file.save("files/" + fileName)
    await sftp_put_async(ssh, "files/" + fileName, filePath)
    os.remove("files/" + fileName)

    
    return fileName

async def task_delete_sftp(file_path, id):
    file_path = file_path + str(id)
    if not await sftp_stat_async(ssh, file_path):
        return False
    await sftp_removeDir_async(ssh, file_path)
    return True

async def user_task_delete(file_path, idUser, idTask):
    file_path = file_path + str(idTask) + "/" + str(idUser)
    if not await sftp_stat_async(ssh, file_path):
        return False
    
    await sftp_removeDir_async(ssh, file_path)

    return True

async def user_task_createDir(file_path, id):
    file_path = file_path + str(id)

    if await sftp_stat_async(ssh, file_path):
            return False
    
    ssh.open_sftp().mkdir(file_path)

    return True    