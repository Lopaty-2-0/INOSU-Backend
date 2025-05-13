from src.utils.sftp_utils import sftp_remove_async
import asyncio
from app import ssh

async def taskDelete(file_path, id):
    file_path = file_path + str(id)
    await sftp_remove_async(ssh, file_path)
    return "Success"