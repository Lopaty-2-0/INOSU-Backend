import os
import random
import datetime
from src.utils.sftp_utils import sftp_remove, sftp_put, sftp_stat
from app import ssh

def pfp(file_path, user, file):
    state = True
    if not user.profilePicture == "default.jpg":
        try:
            sftp_remove(ssh, file_path + user.profilePicture)
        except:
            user.profilePicture = "default.jpg"
        
    while state:
        fileName = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + chr(random.randint(65,90)) + "." + file.filename.rsplit('.', 1)[1].lower()
        filePath = file_path + fileName
        print(sftp_stat(ssh, filePath))
        
        if not sftp_stat(ssh, file_path + fileName):
            file.filename = fileName
            file.save("files/" + file.filename)
            user.profilePicture = file.filename
            sftp_put(ssh ,"files/" + file.filename ,file_path + file.filename)
            os.remove("files/" + file.filename)
            state = False