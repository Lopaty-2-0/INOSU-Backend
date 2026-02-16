import paramiko
import os

def ssh_connect():
    username = os.getenv("SSH_USERNAME")
    password = os.getenv("SSH_PASSWORD")
    ip = os.getenv("SSH_HOST")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    ssh.connect(ip, username=username, password=password)

    return ssh