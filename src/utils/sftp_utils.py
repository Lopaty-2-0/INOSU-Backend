import asyncio
import os
from stat import S_ISDIR
from src.utils.status_codes import InsufficientStorage

def sftp_remove(ssh, filePath):
    sftp = ssh.open_sftp()
    sftp.remove(filePath)
    sftp.close()

def sftp_put(ssh, filePut, filePath):
    sftp = ssh.open_sftp()

    try:
        sftp.put(filePut, filePath)
    except OSError.errno == 28:
        filename = filePath.split("/")[-1]
        os.remove("files/" + filename)

        raise InsufficientStorage
    finally:
        sftp.close()

def sftp_get(ssh, file_get, filePath):
    try:
        sftp = ssh.open_sftp()
        file = sftp.get(filePath, file_get)
        return file
    except:
        return None
    finally:
        sftp.close()

def sftp_stat(ssh, filePath):
    sftp = ssh.open_sftp()
    try:
        return sftp.stat(filePath)
    except FileNotFoundError:
        return None
    finally:
        sftp.close()

def sftp_removedir_recursive(sftp, path):
    for fileAttr in sftp.listdir_attr(path):
        fullPath = f"{path}/{fileAttr.filename}"
        if S_ISDIR(fileAttr.st_mode):
            sftp_removedir_recursive(sftp, fullPath)
        else:
            sftp.remove(fullPath)
    sftp.rmdir(path)

def sftp_createDir(ssh, filePath):
    sftp = ssh.open_sftp()
    sftp.mkdir(filePath)

async def sftp_remove_async(ssh, filePath):
    await asyncio.to_thread(sftp_remove, ssh, filePath)

async def sftp_put_async(ssh, filePut, filePath):
    await asyncio.to_thread(sftp_put, ssh, filePut, filePath)

async def sftp_get_async(ssh, file_get, filePath):
    return await asyncio.to_thread(sftp_get, ssh, file_get, filePath)

async def sftp_stat_async(ssh, filePath):
    return await asyncio.to_thread(sftp_stat, ssh, filePath)

async def sftp_removeDir_async(ssh, filePath):
    sftp = ssh.open_sftp()
    return await asyncio.to_thread(sftp_removedir_recursive, sftp, filePath)

async def sftp_createDir_async(ssh, filePath):
    return await asyncio.to_thread(sftp_createDir, ssh, filePath)