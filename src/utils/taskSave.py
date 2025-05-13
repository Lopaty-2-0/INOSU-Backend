import os
import asyncio
from src.utils.sftp_utils import sftp_put_async, sftp_stat_async
from app import ssh

async def taskSave(file_path, file, id):
    state = True
    file_path = file_path + str(id)
    if not await sftp_stat_async(ssh, file_path):
        ssh.open_sftp().mkdir(file_path)
    while state:
        fileName = file.filename
        filePath = file_path + "/" + fileName

        if not await sftp_stat_async(ssh, filePath):
            
            file.save("files/" + fileName)
            await sftp_put_async(ssh, "files/" + fileName, filePath)
            os.remove("files/" + fileName)
            state = False
    
    return fileName