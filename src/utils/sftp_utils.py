import asyncio
from stat import S_ISDIR

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

def sftp_stat(ssh, file_path):
    sftp = ssh.open_sftp()
    try:
        return sftp.stat(file_path)
    except FileNotFoundError:
        return None
    finally:
        sftp.close()

def sftp_removedir_recursive(ssh, path):
    sftp = ssh.open_sftp()

    try:
        try:
            sftp.listdir(path)
        except FileNotFoundError:
            return
        for item in sftp.listdir_attr(path):
            full_path = f"{path}/{item.filename}"
            if S_ISDIR(item.st_mode):
                sftp_removedir_recursive(sftp, full_path)
            else:
                sftp.remove(full_path)

        sftp.rmdir(path)
    finally:
        sftp.close()

async def sftp_remove_async(ssh, file_path):
    await asyncio.to_thread(sftp_remove, ssh, file_path)

async def sftp_put_async(ssh, file_put, file_path):
    await asyncio.to_thread(sftp_put, ssh, file_put, file_path)

async def sftp_get_async(ssh, file_get, file_path):
    return await asyncio.to_thread(sftp_get, ssh, file_get, file_path)

async def sftp_stat_async(ssh, file_path):
    return await asyncio.to_thread(sftp_stat, ssh, file_path)

async def sftp_removeDir_async(ssh, file_path):
    return await asyncio.to_thread(sftp_removedir_recursive, ssh, file_path)