import os
import random
import datetime
def pfp(file_path, user, file):
    if not user.profilePicture == "default.jpg":
        try:
            os.remove(file_path + user.profilePicture)
        except:
            user.profilePicture = "default.jpg"
            print("File not found, profile picture changed to default")
            return
    file.filename =  datetime.datetime.now().strftime("%Y%m%d%H%M%S") + chr(random.randint(65,90)) + "." + file.filename.rsplit('.', 1)[1].lower()
    file.save(file_path + file.filename )
    user.profilePicture = file.filename