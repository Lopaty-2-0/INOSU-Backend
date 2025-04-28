import os
import random
import datetime
import asyncio
from src.utils.sftp_utils import sftp_remove_async, sftp_put_async, sftp_stat_async
from app import ssh

async def pfpSave(file_path, user, file):
    state = True
    
    if not user.profilePicture == "default.jpg":
        try:
            await sftp_remove_async(ssh, file_path + user.profilePicture)  
        except:
            user.profilePicture = "default.jpg"

    while state:
        fileName = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + chr(random.randint(65, 90)) + "." + file.filename.rsplit('.', 1)[1].lower()
        filePath = file_path + fileName

        if not await sftp_stat_async(ssh, filePath):
            
            file.save("files/" + fileName)
            await sftp_put_async(ssh, "files/" + fileName, file_path + fileName)
            os.remove("files/" + fileName)
            user.profilePicture = fileName
            state = False