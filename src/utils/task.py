import os
from src.utils.sftp_utils import sftp_put_async, sftp_stat_async, sftp_removeDir_async, sftp_remove_async, sftp_createDir_async
from app import ssh, task_path
from src.models.Task import Task
from app import db, hmac_ip
from src.utils.token import generate_hmac_token
import shlex

async def task_save_sftp(file, id, guarantor):
    if not await sftp_stat_async(ssh, task_path):
        ssh.open_sftp().mkdir(task_path)

    filePath = task_path + str(guarantor) + "/" + str(id)
    
    if not await sftp_stat_async(ssh, task_path + str(guarantor)):
        ssh.open_sftp().mkdir(task_path + str(guarantor))

    if not await sftp_stat_async(ssh, filePath):
        await task_createDir(id, guarantor)

    fileName = file.filename
    filePath = filePath + "/" + fileName

    if await sftp_stat_async(ssh, filePath):
        await sftp_remove_async(ssh, filePath)
        
    file.save("files/" + fileName)
    await sftp_put_async(ssh, "files/" + fileName, filePath)
    os.remove("files/" + fileName)

    
    return fileName

async def task_createDir(id, guarantor):
    filePath = task_path + str(guarantor) + "/" + str(id)
    if await sftp_stat_async(ssh, filePath):
        return False
    if not await sftp_stat_async(ssh, task_path):
        await sftp_createDir_async(ssh, filePath)
    if not await sftp_stat_async(ssh, task_path + str(guarantor)):
        await sftp_createDir_async(ssh, task_path + str(guarantor))
    await sftp_createDir_async(ssh, filePath)
    
    return True

async def task_delete_sftp(id, guarantor):
    filePath = task_path + str(guarantor) + "/" + str(id)
    if not await sftp_stat_async(ssh, filePath):
        return False
    await sftp_removeDir_async(ssh, filePath)
    return True

def make_task(file, name, guarantor, deadline, points, endDate, startDate, type):
    task = Task.query.filter_by(guarantor = guarantor).order_by(Task.id.desc()).first()
    id = task.id + 1 if task else 1

    newTask = Task(name=name, startDate=startDate, endDate=endDate,guarantor=guarantor, task = file, type = type, points = points, deadline = deadline, id = id)
    db.session.add(newTask)

    rel_path = task_path + str(guarantor) + "/" + str(id)

    message = f"/uploads/{rel_path}/"
    token = generate_hmac_token(message)

    return newTask, id, token, hmac_ip + message

async def update_task(guarantor, id, file, file2):
    if not await sftp_stat_async(ssh, task_path + str(guarantor) + "/" + str(id)):
        return False
    
    if await sftp_stat_async(ssh, task_path + str(guarantor) + "/" + str(id) + "/" + file2):
        await sftp_remove_async(ssh, task_path + str(guarantor) + "/" + str(id) + "/" + file2)

    file.save("files/" + file.filename)
    await sftp_put_async(ssh, "files/" + file.filename, task_path + str(guarantor) + "/" + str(id) + "/" + file.filename)
    os.remove("files/" + file.filename)

def complete_upload(task, guarantor, id):
    rel_path = task_path + str(guarantor) + "/" + str(id) + "/" + task
    safe_path = shlex.quote(rel_path)

    stdin, stdout, stderr = ssh.exec_command(
        f"/home/assembler/assemble_chunks.sh {safe_path}"
    )

    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        return False

    return True
