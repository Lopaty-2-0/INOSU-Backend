
from app import ssh, task_path
from src.models.Task import Task
from app import db, hmac_ip
from src.utils.token import generate_hmac_token
import shlex

def make_task(file, name, guarantor, deadline, points, endDate, startDate, type):
    task = Task.query.filter_by(guarantor = guarantor).order_by(Task.id.desc()).first()
    id = task.id + 1 if task else 1

    newTask = Task(name=name, startDate=startDate, endDate=endDate,guarantor=guarantor, task = file, type = type, points = points, deadline = deadline, id = id)
    db.session.add(newTask)
    db.session.commit()

    token, uploadUrl = upload_task(file, guarantor, id)

    return newTask, id, token, uploadUrl

def delete_upload_task(task, guarantor, id):
    relPath = task_path + str(guarantor) + "/" + str(id) + "/" + task
    safePath = shlex.quote(relPath)

    stdin, stdout, stderr = ssh.exec_command(
        f"/home/assembler/remove_final.sh {safePath}"
    )

    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        return False

    return True

def upload_task(task, guarantor, id):
    relPath = task_path + str(guarantor) + "/" + str(id)

    message = f"/uploads/{relPath}/{task}"
    token = generate_hmac_token(message)

    return token, hmac_ip + message