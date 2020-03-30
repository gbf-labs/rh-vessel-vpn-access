import os, sys
import subprocess
from datetime import datetime
import time
import paramiko


VPN_TYPE = [
    'GBF',
    'RH',
    'CLIENT',
    'VESSEL',
]

ACCOUNT_OS = {
    'LINUX': {
        'conf_extension': 'conf'
     },
    'WINDOWS': {
        'conf_extension': 'ovpn'
     },
}


class SSH_Vessel_Main:

    def __init__(self,command):
        self.hostname = '172.18.0.3'
        self.port = 22
        self.username = 'root'
        self.password = '1234'
        self.command = command
        self.ssh_client = None

        self.another_init()

    def another_init(self):
        print('[START] another_init:')
        self.ssh_client = paramiko.SSHClient()                                   # create SSHClient instance
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    # AutoAddPolicy automatically adding the hostname and new host key
        self.ssh_client.load_system_host_keys()
        try:
            self.ssh_client.connect(self.hostname, self.port, self.username, self.password)
        except paramiko.ssh_exception.SSHException as e:
            print('IP: {} not found in known_hosts.'.format(self.hostname))
            raise e
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print('Cannot connect to IP: {}'.format(self.hostname))
            raise e

    def run_ssh(self):
        print('[START] run_ssh:')
        print(self.command)
        stdin, stdout, stderr = self.ssh_client.exec_command(self.command)
        out = '\n'.join(str(stdout.read()).split('\\n'))
        out_err = '\n'.join(str(stderr.read()).split('\\n'))
        print('[NEXT] run_ssh:')
        print(out)
        if out_err.strip():
            print(out_err)



if __name__  == '__main__':

    ssh_client = SSH_Vessel_Main('ip  addr')
    ssh_client.run_ssh()


