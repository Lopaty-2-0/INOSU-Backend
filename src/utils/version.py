from src.models.Version_Team import Version_Team
from app import db, task_path, hmac_ip, ssh
from src.utils.token import generate_hmac_token
import shlex


def make_version(idTask, idTeam, file, guarantor):
    if not Version_Team.query.filter_by(idTask = idTask, idTeam = idTeam, guarantor = guarantor).first():
        id = 1
    else:
        id = Version_Team.query.filter_by(idTask=idTask, idTeam = idTeam, guarantor = guarantor).order_by(Version_Team.idVersion.desc()).first().idVersion + 1

    
    newVersion = Version_Team(idVersion = id, idTask = idTask, elaboration = file.filename, idTeam = idTeam, guarantor = guarantor)
    
    db.session.add(newVersion)
    db.session.commit()

    relPath = task_path + str(guarantor) + "/" + str(idTask) + "/" + str(idTeam) + "/" + str(id)

    message = f"/uploads/{relPath}/{file}"
    token = generate_hmac_token(message)

    return hmac_ip + message + "?token=" + token

def delete_upload_version(idTask, idTeam, file, guarantor, idVersion):
    relPath = task_path + str(guarantor) + "/" + str(idTask) + "/" + str(idTeam) + "/" + str(idVersion) + "/" + file
    safePath = shlex.quote(relPath)

    stdin, stdout, stderr = ssh.exec_command(
        f"/home/assembler/remove_final.sh {safePath}"
    )

    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        return False

    return True