import os
import random
import datetime
import asyncio
from src.utils.sftp_utils import sftp_put_async, sftp_stat_async
from app import ssh

async def taskSave(file_path, file):
    state = True

    while state:
        fileName = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + chr(random.randint(65, 90)) + "." + file.filename.rsplit('.', 1)[1].lower()
        filePath = file_path + fileName

        if not await sftp_stat_async(ssh, filePath):
            
            file.save("files/" + fileName)
            await sftp_put_async(ssh, "files/" + fileName, file_path + fileName)
            os.remove("files/" + fileName)
            state = False
    
    return fileName