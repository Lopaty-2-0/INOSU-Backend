def sftp_remove(ssh, file_path):
    sftp = ssh.open_sftp()
    sftp.remove(file_path)
    sftp.close()

def sftp_put(ssh, file_put, file_path):
    sftp = ssh.open_sftp()
    sftp.put(file_put, file_path)
    sftp.close()

def sftp_get(ssh, file_get, file_path):
    try:
        sftp = ssh.open_sftp()
        file = sftp.get(file_path, file_get)
        return file
    except:
        return None
    finally:
        sftp.close()

def sftp_stat(ssh, file_stat):
    sftp = ssh.open_sftp()
    try:
        return sftp.stat(file_stat)
    except FileNotFoundError:
        return None
    finally:
        sftp.close()