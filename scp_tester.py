import paramiko
from paramiko import SSHClient
from scp import SCPClient

# ssh = SSHClient()
# ssh.load_system_host_keys()
# ssh.connect('172.18.0.2')

hostname = '172.18.0.2'
port = 22
username = 'root'
password = '1234'
command = ''
ssh_client = None

ssh_client = paramiko.SSHClient()                                   # create SSHClient instance
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    # AutoAddPolicy automatically adding the hostname and new host key
ssh_client.load_system_host_keys()
ssh_client.connect(hostname, port, username, password)

with SCPClient(ssh_client.get_transport()) as scp:
    scp.put('/home/scp-file', '/home/ssh-file-x')
    # scp.get('test2.txt')
