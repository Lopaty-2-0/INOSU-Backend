import os
import random
import datetime
import asyncio
from src.utils.sftp_utils import sftp_remove_async, sftp_put_async, sftp_stat_async, sftp_createDir_async
from app import ssh

async def pfp_save(filePath, user, file):
    state = True

    if not await sftp_stat_async(ssh, filePath):
        await sftp_createDir_async(ssh, filePath)

    while state:
        fileName = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + chr(random.randint(65, 90)) + "." + file.filename.rsplit('.', 1)[1].lower()
        filePath = filePath + fileName

        if not await sftp_stat_async(ssh, filePath):
            
            file.save("files/" + fileName)
            await sftp_put_async(ssh, "files/" + fileName, filePath + fileName)
            os.remove("files/" + fileName)
            state = False

        if not user.profilePicture == "default.jpg":
            try:
                await sftp_remove_async(ssh, filePath + user.profilePicture)  
            except:
                user.profilePicture = "default.jpg"
                
        user.profilePicture = fileName

async def pfp_delete(filePath, user):
    if not user.profilePicture == "default.jpg":
        try:
            await sftp_remove_async(ssh, filePath + user.profilePicture)  
        except:
            return
