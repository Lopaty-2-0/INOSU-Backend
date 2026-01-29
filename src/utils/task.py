import os
from src.utils.sftp_utils import sftp_put_async, sftp_stat_async, sftp_removeDir_async, sftp_remove_async, sftp_createDir_async
from app import ssh, task_path
from src.models.Task import Task
from app import db

async def task_save_sftp(file, id, guarantor):
    state = True

    if not await sftp_stat_async(ssh, task_path):
        ssh.open_sftp().mkdir(task_path)

    file_path = task_path + str(guarantor) + "/" + str(id)
    
    if not await sftp_stat_async(ssh, task_path + str(guarantor)):
        ssh.open_sftp().mkdir(task_path + str(guarantor))

    if not await sftp_stat_async(ssh, file_path):
        task_createDir(id, guarantor)

    fileName = file.filename
    filePath = file_path + "/" + fileName

    if await sftp_stat_async(ssh, filePath):
        await sftp_remove_async(ssh, file_path)
        
    file.save("files/" + fileName)
    await sftp_put_async(ssh, "files/" + fileName, filePath)
    os.remove("files/" + fileName)

    
    return fileName

async def task_createDir(id, guarantor):
    file_path = task_path + str(guarantor) + "/" + str(id)
    if await sftp_stat_async(ssh, file_path):
        return False
    if not await sftp_stat_async(ssh, task_path):
        await sftp_createDir_async(ssh, file_path)
    if not await sftp_stat_async(ssh, task_path + str(guarantor)):
        await sftp_createDir_async(ssh, task_path + str(guarantor))
    await sftp_createDir_async(ssh, file_path)
    
    return True

async def task_delete_sftp(id, guarantor):
    file_path = task_path + str(guarantor) + "/" + str(id)
    if not await sftp_stat_async(ssh, file_path):
        return False
    await sftp_removeDir_async(ssh, file_path)
    return True

async def make_task(file, name, guarantor, deadline, points, endDate, startDate, type):
    task = Task.query.filter_by(guarantor = guarantor).order_by(Task.id.desc()).first()
    id = task.id + 1 if task else 1

    newTask = Task(name=name, startDate=startDate, endDate=endDate,guarantor=guarantor, task = file.filename, type = type, points = points, deadline = deadline, id = id)
    db.session.add(newTask)

    if await sftp_stat_async(ssh, task_path + str(id)):
        await task_delete_sftp(id, guarantor)
        
    await task_save_sftp(file, id, guarantor)

    db.session.commit()

    return newTask, id