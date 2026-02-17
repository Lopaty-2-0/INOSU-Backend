import random
import datetime
import shlex
from app import pfp_path, hmac_ip, ssh
from src.utils.token import generate_hmac_token

def pfp_save(file):
    if len(file.rsplit('.', 1)) < 2:
        return False

    fileName = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + chr(random.randint(65, 90)) + "." + file.rsplit('.', 1)[1].lower()

    message = f"/uploads/{pfp_path}{fileName}"
    token = generate_hmac_token(message, max_size=2 * 1024 * 1024)

    return hmac_ip + message + "?token=" + token 

def pfp_check(pfp):
    relPath = pfp_path + pfp

    safePath = shlex.quote(relPath)

    stdin, stdout, stderr = ssh.exec_command(
        f"/home/assembler/check_final.sh {safePath}" #TODO: změnit jakmile to udělá
    )

    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        return False

    return True

def pfp_delete(pfp):
    relPath = pfp_path + pfp

    safePath = shlex.quote(relPath)

    stdin, stdout, stderr = ssh.exec_command(
        f"/home/assembler/remove_final.sh {safePath}"
    )

    exit_status = stdout.channel.recv_exit_status()

    if exit_status != 0:
        return False

    return True