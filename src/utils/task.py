import os
from src.utils.sftp_utils import sftp_put_async, sftp_stat_async, sftp_removeDir_async, sftp_remove_async
from app import ssh, task_path

async def task_save_sftp(file, id):
    state = True

    if not await sftp_stat_async(ssh, task_path):
        ssh.open_sftp().mkdir(task_path)

    file_path = task_path + str(id)

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

async def task_delete_sftp(id):
    file_path = task_path + str(id)
    if not await sftp_stat_async(ssh, file_path):
        return False
    await sftp_removeDir_async(ssh, file_path)
    return True