#!/usr/bin/env python3
import argparse
import os, sys
# sys.path.append(os.path.dirname(os.getcwd()))
import subprocess
from library.postgresql_queries import PostgreSQL
from datetime import datetime
import time
import paramiko
from scp import SCPClient
import requests
import json
import random


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

class SSH_Vessel_Main_SCP:

    def __init__(self, account_filename):
        self.web_server_ip = '172.18.0.3'
        self.port = 22
        self.username = 'root'
        self.password = '1234'
        self.ssh_client = None
        self.account_filename = account_filename

    def ssh_to_server(self):
        print('[START] another_init:')
        self.ssh_client = paramiko.SSHClient()                                   # create SSHClient instance
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    # AutoAddPolicy automatically adding the hostname and new host key
        self.ssh_client.load_system_host_keys()
        try:
            self.ssh_client.connect(self.web_server_ip, self.port, self.username, self.password)
        except paramiko.ssh_exception.SSHException as e:
            print('IP: {} not found in known_hosts. / invalid credentials'.format(self.web_server_ip))
            raise e
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print('Cannot connect to IP: {}'.format(self.web_server_ip))
            raise e

    def scp_file(self, postgresql_query, id_vpn_access_requests):
        print('[START] scp_file:')
        print('file_source_path:', self.account_filename)

        #SCP FILE
        try:
            file_source_path = self.account_filename
            with SCPClient(self.ssh_client.get_transport()) as scp:
                with open(self.account_filename, 'rb') as file:
                    scp.putfo(file, file_source_path)
        except:
            conditions = []
            conditions.append({
                "col": "id",
                "con": "=",
                "val": id_vpn_access_requests
            })
            data = {}
            data['status'] = 'CONN-ERR'
            data['status_details'] = 'ERR: {} - {}'.format(self.web_server_ip, str(sys.exc_info())[:401].replace('\'', '\"'))
            data['request_finish_date'] = datetime.fromtimestamp(time.time())
            postgresql_query.update('vpn_access_requests', data, conditions)

        print('[DONE] scp_file:')


    def test_ssh_to_server(self, postgresql_query, id_vpn_access_requests):
        try:
            self.ssh_to_server()
            return True
        except:
            conditions = []
            conditions.append({
                "col": "id",
                "con": "=",
                "val": id_vpn_access_requests
            })
            data = {}
            data['status'] = 'CONN-ERR'
            data['status_details'] = 'ERR: {} - {}'.format(self.web_server_ip, str(sys.exc_info())[:401].replace('\'', '\"'))
            data['request_finish_date'] = datetime.fromtimestamp(time.time())
            postgresql_query.update('vpn_access_requests', data, conditions)
            return False

    def scp_process(self):
        pass
        '''
            account_filename = os.path.join(
                                    Vpn_Access.zipfiles_main_path,
                                    Vpn_Access.set_account_filename(self.vpn_type, self.account_id, self.account_name)
                            )
            account_filename += '.zip'
            vpn_access_scp = SSH_Vessel_Main_SCP(
                account_filename=account_filename
            )

            #TEST SSH CONNECTION FIRST
            if not vpn_access_scp.test_ssh_to_server(self.postgresql_query, id_vpn_access_requests):
                return False

            #VPN-CREATION
            vpn_access.create_static_ip()

            vpn_access_scp.scp_file(self.postgresql_query, id_vpn_access_requests)
            vpn_access_scp.ssh_client.close()
        '''

class SSH_Server:

    def __init__(self, server_ip, port, username, password):
        self.server_ip = server_ip
        self.port = port
        self.username = username
        self.password = password
        self.ssh_client = None
        self.connection_error = None
        self.stdout = None
        self.stderr = None

    def ssh_to_server(self):
        print('[START] ssh_to_server:{}'.format(self.server_ip))
        self.ssh_client = paramiko.SSHClient()                                   # create SSHClient instance
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    # AutoAddPolicy automatically adding the server_ip and new host key
        self.ssh_client.load_system_host_keys()
        try:
            self.ssh_client.connect(self.server_ip, self.port, self.username, self.password) #, look_for_keys=False,  allow_agent=False)
        except paramiko.ssh_exception.SSHException as e:
            self.connection_error = 'IP: {} not found in known_hosts. / INVALID CREDENTIALS.'.format(self.server_ip)
            print(self.connection_error)
            print(e)
            # raise e
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            self.connection_error = 'Cannot connect to IP: {}'.format(self.server_ip)
            print(self.connection_error)
            # raise e
        except:
            self.connection_error = str(sys.exc_info())
            print(self.connection_error)


    def run_command(self, command):
        print('[START] run_command:')
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        self.stdout = '\n'.join(str(stdout.read()).split('\\n')) or ''
        self.stderr = '\n'.join(str(stderr.read()).split('\\n')) or ''
        print('-------------------output')
        print(self.stdout)
        print('-------------------output')
        if self.stderr.strip():
            print(self.stderr)
        print('[DONE] run_command:')
        return self.stdout, self.stderr

class Vpn_Access_RealVessel:

    openvpn_path           = '/etc/openvpn'
    crt_file_path           = 'SAMPLE_CRT_FILE.conf'

    def __init__(self,
            vessel_ip_address,
            vessel_name,
            vessel_username,
            vessel_password,
            vessel_port,
            vessel_imo,
            account_id,
            account_ip_address,
            token,
            job_id,
            callback_url,
            vpn_type,
            action='ADD',
        ):

        print("[Vpn_Access_RealVessel]")
        self.vessel_ip_address = vessel_ip_address
        self.vessel_username = vessel_username
        self.vessel_password = vessel_password
        self.vessel_port = vessel_port
        self.account_id = account_id
        self.account_ip_address = account_ip_address
        self.token = token
        self.job_id = job_id
        self.table_id = None
        self.callback_url = callback_url
        self.vpn_type = vpn_type

        self.self_check_status = True
        self.self_check_details = ''
        self.vessel_name = vessel_name
        # self.crt_file_path = self.vessel_name + '.conf'
        #self.crt_file_path = 'rh_{}.conf'.format(vessel_imo)
        # PENN
        self.crt_file_path = 'VESSEL_{}.conf'.format(vessel_imo)
        self.action = ''

        self.is_ssh_connection_error = 0
        self.postgresql_query = PostgreSQL()
        
        if action == 'ADD':
            self.self_check()

    def self_check(self):
        self.postgresql_query.connection()
        sql_str = "SELECT 'EXIST' as ACTIVE FROM account_vpn_access WHERE account_id = {} AND vpn_type='{}' AND is_active=1 ".format(self.account_id, self.vpn_type)
        result = self.postgresql_query.query_fetch_one(sql_str)
        print(sql_str)
        self.postgresql_query.close_connection()

        if hasattr(result, 'get'):
            self.self_check_status = True
        else:
            self.self_check_status = False
            self.self_check_details = "Doesn't have existing active Vessel VPN."
            print("[ERROR] Doesn't have existing active Vessel VPN.")


    def add_access(self):
        print("[START] - add_access.")

        self.action = 'ADD'
        message = ''
        status = '' # ok | failed

        created_id = None

        self.postgresql_query.connection()
        sql_str = "select * from vpn_access_real_vessel_requests where job_id={}".format(self.job_id)
        result = self.postgresql_query.query_fetch_one(sql_str)
        self.postgresql_query.close_connection()

        if hasattr(result, 'get'):
            created_id = result['job_id']
            self.vessel_ip_address = result['vessel_ip_address']
            self.vessel_username = result['vessel_username']
            self.vessel_password = result['vessel_password']
            self.vessel_port = result['vessel_port']
            self.account_id = result['account_id']
            self.account_ip_address = result['account_vpn_ip']
            self.token = result['token']
            self.job_id = result['job_id']
            self.table_id = result['id']
            self.callback_url = result['callback_url']

        if not created_id:
            data = {}
            data['request_type'] = 'add-access'
            data['job_id'] = self.job_id
            data['vessel_ip_address'] = self.vessel_ip_address
            data['vessel_port'] = self.vessel_port
            data['vessel_username'] = self.vessel_username
            data['vessel_password'] = self.vessel_password
            data['token'] = self.token
            data['callback_url'] = self.callback_url
            data['account_id'] = self.account_id
            data['account_vpn_ip'] = self.account_ip_address
            data['request_start_date'] = datetime.fromtimestamp(time.time())

            self.postgresql_query.connection()
            created_id = self.postgresql_query.insert('vpn_access_real_vessel_requests', data, table_id='id')
            self.table_id = created_id
            self.postgresql_query.close_connection()
            print('+'*100)
            print('created_id:', created_id)

        if not created_id:
            status = 'failed'
            message = 'Problem on inserting/getting data in vpn_access_real_vessel_requests.'
        elif not self.self_check_status:
            status = 'failed'
            message = self.self_check_details
        else:
            content = 'route {}'.format(self.account_ip_address)
            append_content = "echo '{}' >> {}".format(content, self.crt_file_path)
            commands = [
                "cd {}".format(Vpn_Access_RealVessel.openvpn_path)
                ,append_content
                ,"cat {}".format(self.crt_file_path)
            ]
            command = ' && '.join(commands)
            print('command: ', command)

            ssh_server = SSH_Server(
                server_ip = self.vessel_ip_address,
                username = self.vessel_username,
                password = self.vessel_password,
                port = self.vessel_port,
            )
            ssh_server.ssh_to_server()

            if ssh_server.connection_error:
                message = ssh_server.connection_error
                status = 'failed'
                self.is_ssh_connection_error = 1
            else:
                command_checker = ' && '.join([
                    "cd {}".format(Vpn_Access_RealVessel.openvpn_path)
                    ,"cat {}".format(self.crt_file_path)
                ])
                stdout, stderr = ssh_server.run_command(command_checker)

                if self.account_ip_address in stdout:
                    message = 'IP {} is already in Vessel {}'.format(self.account_ip_address, self.vessel_ip_address)
                    status = 'ok' # status = 'failed'
                else:
                    stdout, stderr = ssh_server.run_command(command)
                    #CHECK IP IN THE OUTPUT
                    if self.account_ip_address in stdout:
                        message = 'Successfull adding IP to Vessel {}'.format(self.vessel_ip_address)
                        status = 'ok'
                        #RESTART OPENVPN SERVER
                        command_restart = "sudo service openvpn restart"
                        if self.vessel_username == 'root':
                            command_restart = "service openvpn restart"
                        ssh_server.run_command(command_restart)

                    else:
                        message = 'Not able to add Ip to Vessel: {}'.format(self.vessel_ip_address)
                        status = 'failed'

                #SUCCESS: ADD DATA TO ACCOUNT_VPN_ACCESS_REAL_VESSEL
                if status == 'ok':
                        print('SUCCESS: ADD DATA TO ACCOUNT_VPN_ACCESS_REAL_VESSEL')
                        data = {}
                        data['add_job_id'] = self.job_id
                        data['remove_job_id'] = '0'
                        data['account_ip_address'] = self.account_ip_address
                        data['account_id'] = self.account_id
                        data['is_active'] = 1
                        data['date_created'] = datetime.fromtimestamp(time.time())

                        self.postgresql_query.connection()
                        created_id = self.postgresql_query.insert('account_vpn_access_real_vessel', data, table_id='id')
                        print('self.table_id', self.table_id)
                        self.postgresql_query.close_connection()


        self.callback(status, message)
        print("[END] - add_access.")

    def remove_access(self):
        print("[START] - remove_access.")

        self.action = 'REMOVE'
        message = ''
        status = '' # ok | failed

        data = {}
        data['request_type'] = 'remove-access'
        data['job_id'] = self.job_id
        data['vessel_ip_address'] = self.vessel_ip_address
        data['vessel_port'] = self.vessel_port
        data['vessel_username'] = self.vessel_username
        data['vessel_password'] = self.vessel_password
        data['token'] = self.token
        data['callback_url'] = self.callback_url
        data['account_id'] = self.account_id
        data['account_vpn_ip'] = self.account_ip_address
        data['request_start_date'] = datetime.fromtimestamp(time.time())

        self.postgresql_query.connection()
        created_id = self.postgresql_query.insert('vpn_access_real_vessel_requests', data, table_id='id')
        if not created_id:

            # INIT CONDITION
            conditions = []           
 
            # CONDITION FOR QUERY
            conditions.append({
                "col": "job_id",
                "con": "=",
                "val": self.job_id
                })

            self.postgresql_query.update('vpn_access_real_vessel_requests', data, conditions)
           
            self.postgresql_query.connection()
 
            sql_str = "SELECT id FROM vpn_access_real_vessel_requests WHERE job_id ={0}".format(self.job_id)
            created_id = self.postgresql_query.query_fetch_one(sql_str)
            created_id =  created_id['id']
            
            self.postgresql_query.close_connection()
            print("*"*100)
            print(created_id)
            print("*"*100)

        self.table_id = created_id
        print('self.table_id', self.table_id)
        self.postgresql_query.close_connection()

        if not created_id:
            status = 'failed'
            message = 'Problem on inserting data in vpn_access_real_vessel_requests.'
        elif not self.self_check_status:
            status = 'failed'
            message = self.self_check_details
        else:
            content = 'route {}'.format(self.account_ip_address)
            append_content = "sudo sed -i '/{}/d' {}".format(content, self.crt_file_path)
            commands = [
                "cd {}".format(Vpn_Access_RealVessel.openvpn_path)
                ,append_content
                ,"cat {}".format(self.crt_file_path)
            ]
            command = ' && '.join(commands)
            # print('command: ', command)

            ssh_server = SSH_Server(
                server_ip = self.vessel_ip_address,
                username = self.vessel_username,
                password = self.vessel_password,
                port = self.vessel_port,
            )
            ssh_server.ssh_to_server()

            if ssh_server.connection_error:
                message = ssh_server.connection_error
                status = 'failed'
                self.is_ssh_connection_error = 1
            else:
                command_checker = ' && '.join([
                    "cd {}".format(Vpn_Access_RealVessel.openvpn_path)
                    ,"cat {}".format(self.crt_file_path)
                ])
                stdout, stderr = ssh_server.run_command(command_checker)

                if self.account_ip_address not in stdout:
                    message = 'IP {} is not present in Vessel {} config file'.format(self.account_ip_address, self.vessel_ip_address)
                    status = 'ok' # status = 'failed'
                else:
                    stdout, stderr = ssh_server.run_command(command)
                    #CHECK IP IN THE OUTPUT
                    if self.account_ip_address not in stdout:
                        message = 'Successfull removing IP to Vessel {}'.format(self.vessel_ip_address)
                        status = 'ok'

                        #RESTART OPENVPN SERVER
                        command_restart = "sudo service openvpn restart"
                        if self.vessel_username == 'root':
                            command_restart = "service openvpn restart"
                        ssh_server.run_command(command_restart)

                    else:
                        message = 'Not able to remove Ip to Vessel: {}'.format(self.vessel_ip_address)
                        status = 'failed'

                if status == 'ok':
                    #SUCCESS REMOVE DATA TO ACCOUNT_VPN_ACCESS_REAL_VESSEL
                    conditions = []
                    conditions.append({
                        "col": "account_ip_address",
                        "con": "=",
                        "val": self.account_ip_address
                    })
                    conditions.append({
                        "col": "account_id",
                        "con": "=",
                        "val": self.account_id
                    })
                    conditions.append({
                        "col": "is_active",
                        "con": "=",
                        "val": 1
                    })
                    data = {}
                    data['remove_job_id'] = self.job_id
                    data['is_active'] = 0
                    data['last_update_date'] = datetime.fromtimestamp(time.time())
                    self.postgresql_query.update('account_vpn_access_real_vessel', data, conditions)


        self.callback(status, message)
        print("[END] - remove_access.")

    def callback(self, status, message):
        print("[START] - callback.")

        ## CALLBACK
        status_code = ''
        try:
            headers = {}
            headers['content-type'] = 'application/json'
            headers['token'] = str(self.token)
            headers['jobid'] = str(self.job_id)
            data = {
                'job_id': self.job_id,
                'status': status,
                'message': message,
                'directory': '',
                'action': self.action,
                'vpn_type': self.vpn_type,
                'ip': self.vessel_ip_address
            }
            print("*"*100)
            print("callback_url: ", self.callback_url)
            print("headers: ", headers)
            print("data: ", data)
            print("*"*100)
            r = requests.put(self.callback_url, data=json.dumps(data), headers=headers)
            status_code = r.status_code
        except:
            print('[CALL-BACK-ERROR] >')
            print(sys.exc_info())
            sys.exit(0)

        conditions = []
        conditions.append({
            "col": "id",
            "con": "=",
            "val": self.table_id
        })
        message = message or ''
        data = {}
        data['request_finish_date'] = datetime.fromtimestamp(time.time())
        data['status'] = status
        data['status_details'] = message[:400].replace('\'', ' ')
        data['is_ssh_connection_error'] = self.is_ssh_connection_error
        data['callback_status'] = status_code
        data['request_tries'] = 1

        self.postgresql_query.update('vpn_access_real_vessel_requests', data, conditions)

        print("[END] - callback.")

class Vpn_Access_Main:

    def __init__(self,
                 job_id, callback_url, token, account_id,
                 vpn_type, vpn_request_type, account_name=None,
                 account_os=None, real_vessel_manual_creation=False):

        self.job_id = job_id
        self.callback_url = callback_url
        self.token = token
        self.account_id = account_id
        self.account_name = account_name
        self.vpn_type = vpn_type
        self.vpn_request_type = vpn_request_type
        self.account_os = account_os
        self.postgresql_query = PostgreSQL()

        #For Real-Vessel Manual VPN Creation
        self.real_vessel_manual_creation = real_vessel_manual_creation

        #For Vessel VPN
        self.python_executable_path = '/usr/bin/python3.5'
        self.python_scripts_path = '/app/'


    def run(self):
        print('[START] Vpn_Access/run:')

        vpn_type_options = [
            'CLIENT',
            'UNKNOWN',
            'RH',
            'GBF',
            'VGBF',
            'VRH',
            'VCLIENT',
            'VESSEL',
            'VUNKNOWN',
        ]


        # if self.vpn_type in ['VESSEL', 'RH', 'CLIENT', 'UNKNOWN', 'GBF']:
        if self.vpn_type in vpn_type_options:

            status = 'ok' # ok | failed
            status_details = ''
            action = self.vpn_request_type
            directory = ''

            #ADD HERE THE VPN_ACCESS_REQUEST TABLE
            self.postgresql_query.connection()
            conditions = []
            data = {}
            data['job_id'] = self.job_id
            data['vpn_type']  = self.vpn_type
            data['vpn_request_type']  = self.vpn_request_type
            data['account_id'] = self.account_id
            data['account_name'] = self.account_name
            data['account_os'] = self.account_os
            data['request_start_date'] = datetime.fromtimestamp(time.time())
            id_vpn_access_requests = None
            created_ip_addr1 = ''

            try:
                id_vpn_access_requests = self.postgresql_query.insert('vpn_access_requests', data, 'id')
            except:
                id_vpn_access_requests = None
            finally:
                self.postgresql_query.close_connection()
                print("ID_VPN_ACCESS_REQUESTS:", id_vpn_access_requests)
                if not id_vpn_access_requests:
                    status = 'failed'
                    status_details = "[ERROR] Unable to insert in vpn_access_requests table."
                    print(status_details)


            if status == 'ok':
                if self.vpn_request_type == 'CREATE':
                    vpn_access = Vpn_Access_Create(id_vpn_access_requests, self.account_id, self.account_name, self.vpn_type, self.account_os)
                    vpn_access.create_static_ip()
                    directory = vpn_access.zip_file_path
                    status = vpn_access.status
                    status_details = vpn_access.status_details
                    created_ip_addr1 = vpn_access.current_ip_1

                    # ALLOW/DISALLOW FOR USER-VPN (API AND WEB)
                    if status == 'ok' and self.vpn_type in ['CLIENT', 'GBF', 'RH', 'UNKNOWN']:

                        self.postgresql_query.connection()
                        sql_str = "SELECT ip_addr_1, ip_addr_2  FROM account_vpn_access WHERE id_vpn_access_requests = '{}' ".format(id_vpn_access_requests)
                        # input('debug>>>')
                        result = self.postgresql_query.query_fetch_one(sql_str)
                        # input('debug2>>>')
                        self.postgresql_query.close_connection()
                        # input('debug3>>>')

                        ip_addr_1 = result['ip_addr_1']
                        ip_addr_2 = result['ip_addr_2']

                        vpn_ad = Vpn_Access_Create_AllowDisallowed(
                            id_vpn_access_requests,
                            account_id=self.account_id,
                            account_vpn_ip=ip_addr_1,
                        )
                        vpn_ad.add_access()

                elif self.vpn_request_type == 'DELETE':
                    vpn_access_revoke = Vpn_Access_Revoke(id_vpn_access_requests, self.account_id, self.vpn_type)
                    vpn_access_revoke.revoke()
                    status = vpn_access_revoke.status
                    status_details = vpn_access_revoke.status_details

                    # ALLOW/DISALLOW FOR USER-VPN (API AND WEB)
                    if self.vpn_type in ['CLIENT', 'GBF', 'RH', 'UNKNOWN']:
                        self.postgresql_query.connection()
                        sql_str = "SELECT ip_addr_1, ip_addr_2  FROM account_vpn_access WHERE account_id = '{}'  AND is_active=0"\
                                "order by  last_update_date desc limit 1".format(self.account_id)

                        result = self.postgresql_query.query_fetch_one(sql_str)
                        self.postgresql_query.close_connection()

                        # print(sql_str)
                        # print('result:', result)

                        if hasattr(result, 'get'):
                            ip_addr_1 = result['ip_addr_1']
                            ip_addr_2 = result['ip_addr_2']
                            vpn_ad = Vpn_Access_Create_AllowDisallowed(
                                id_vpn_access_requests,
                                account_id=self.account_id,
                                account_vpn_ip=ip_addr_1,
                            )
                            vpn_ad.remove_access()
                        else:
                            status = 'failed'
                            status_details += '\n[Vpn_Access_Create_AllowDisallowed] No Data Found in account_vpn_access.'

            if not self.real_vessel_manual_creation:
                headers = {}
                headers['content-type'] = 'application/json'
                headers['token'] = str(self.token)
                headers['jobid'] = str(self.job_id)

                data = {}
                data['status'] = status
                data['message'] = status_details
                data['directory'] = directory
                data['action'] = action
                data['ip'] = created_ip_addr1
                data['vpn_type'] = self.vpn_type
                res = {}
                status_code = ''

                try:
                    print("*"*100)
                    print("callback_url: ", self.callback_url)
                    print("headers: ", headers)
                    print("data: ", data)
                    print("*"*100)

                    r = requests.put(self.callback_url, data=json.dumps(data), headers=headers)
                    res = r.json()
                    status_code = r.status_code

                except:
                    print('[CALL-BACK-ERROR] >')
                    print(sys.exc_info())
                    sys.exit(0)

                conditions = []
                conditions.append({
                    "col": "id",
                    "con": "=",
                    "val": id_vpn_access_requests
                })
                data = {}
                data['callback_status'] = status_code
                self.postgresql_query.update('vpn_access_requests', data, conditions)

        else:
            print("[ERROR] Unknown VPN-Type. {}".format(self.vpn_type))

class Vpn_Access_Create:

    ccd_path           = '/etc/openvpn/ccd'
    easy_rsa_path      = '/etc/openvpn/easy-rsa/'
    easy_rsa_key_path  = '/etc/openvpn/easy-rsa/keys/'
    zipfiles_main_path = '/home/all_vpn/'


    def __init__(self, id_vpn_access_requests, account_id, account_name, vpn_type, account_os):

        self.id_vpn_access_requests = id_vpn_access_requests
        self.account_id       = account_id
        self.account_name     = account_name
        self.vpn_type         = vpn_type
        self.account_os       = account_os
        self.zip_file_path = None

        self.postgresql_query = PostgreSQL()

        self.conf_default_root_path  = '/home/uvpn/vpn_access' #os.path.join(os.getcwd(), 'WEB_API_VPN_DEFAULT_CONFIGURATION_FILE')
        self.account_filename   = Vpn_Access_Create.set_account_filename(vpn_type, account_id, account_name)
        self.current_ip_1 = None
        self.current_ip_2 = None

        self.self_check_status = True
        self.self_check()

    @property
    def vpn_default_conf_path(self):
        '''Configuration files and vpn_access.py should be in the same folder.'''

        self.postgresql_query.connection()
        sql_str = "SELECT config_file_name FROM vpn_access WHERE vpn_type = '{}' ".format(self.vpn_type)
        result = self.postgresql_query.query_fetch_one(sql_str)
        self.postgresql_query.close_connection()

        if hasattr(result, 'get'):
            config_file_name = result['config_file_name'].strip()
            return os.path.join(self.conf_default_root_path, config_file_name)
        else:
            return None
            # raise ValueError('[ERROR] Unknown Account Type.')


    @staticmethod
    def set_account_filename(vpn_type, account_id, account_name):
        account_filename   = '{}_{:02d}_{}'.format(vpn_type, account_id, account_name)
        
        if vpn_type == 'VESSEL':
            account_filename   = 'VESSEL_{:02d}'.format(account_id)
        print('account_filename:', account_filename)
        return account_filename


    def self_check(self):
        '''CHECKING ALL CAUSES OF POSSIBLE ERRORS.'''

        #VERIFY IF THE USER DOESN'T HAVE EXISTING VPN THAT IS ACTIVE
        self.postgresql_query.connection()
        sql_str = "SELECT COUNT(1) FROM account_vpn_access WHERE account_id={} AND vpn_type='{}' AND is_active=1".\
            format(self.account_id, self.vpn_type)
        count = self.postgresql_query.query_fetch_one(sql_str)
        is_exists = count['count']
        self.postgresql_query.close_connection()
        if is_exists:
            status_details = '[ERROR] this account has existing vpn-access for {} VPN.'.format(self.vpn_type)
            print(status_details)
            conditions = []
            conditions.append({
                "col": "id",
                "con": "=",
                "val": self.id_vpn_access_requests #"CLIENT",
                })
            data = {}
            data['status'] = 'DENIED'
            data['request_finish_date'] = datetime.fromtimestamp(time.time())
            data['status_details'] = status_details
            self.postgresql_query.update('vpn_access_requests', data, conditions)

            self.self_check_status = False

        #CHECK ALL EXISTENCE OF ALL DIRS
        try:
            assert self.vpn_default_conf_path, 'self.vpn_default_conf_path'
            assert os.path.exists(self.ccd_path), 'self.ccd_path'
            assert os.path.exists(self.easy_rsa_path), 'self.easy_rsa_path'
            assert os.path.exists(self.easy_rsa_key_path), 'self.easy_rsa_key_path'
            assert os.path.exists(self.zipfiles_main_path), 'self.zipfiles_main_path'

            assert not os.path.exists(os.path.join(self.ccd_path, self.account_filename)), 'Existing file in ccd.'

            assert self.account_name, 'self.account_name'
            assert self.vpn_type, 'self.vpn_type'
            assert self.account_os, 'self.account_os'

        except:
            status_details = 'ERROR: In VPN_ACCESS.self_check. | '
            status_details += str(sys.exc_info())[:400].replace('\'', '\"')
            print(status_details)

            conditions = []
            conditions.append({
                "col": "id",
                "con": "=",
                "val": self.id_vpn_access_requests #"CLIENT",
                })
            data = {}
            data['status'] = 'DENIED'
            data['request_finish_date'] = datetime.fromtimestamp(time.time())
            data['status_details'] = status_details
            self.postgresql_query.update('vpn_access_requests', data, conditions)

            self.self_check_status = False


    def create_static_ip(self):
        print("RUNNING - create_static_ip.")
        status_failed = 'failed'
        status_ok = 'ok'

        if not self.self_check_status:
            self.status = 'failed'
            self.status_details = "[ERROR] self_check_status."
            return self.id_vpn_access_requests

        self.postgresql_query.connection()
        sql_str = "SELECT COUNT(1) FROM vpn_access where vpn_type ='{}'".format(self.vpn_type)
        count = self.postgresql_query.query_fetch_one(sql_str)
        is_exists = count['count']
        self.postgresql_query.close_connection()

        if not is_exists:
            print("[ERROR] Account type {} doesn't exists.".format(self.vpn_type))
            self.status = 'failed'
            self.status_details = "[ERROR] Account type {} doesn't exists.".format(self.vpn_type)
            return self.id_vpn_access_requests

        filename = os.path.join(self.ccd_path, self.account_filename)

        if os.path.exists(filename):
            print('[ERROR] File Already Exists: {}'.format(filename))
            self.status = 'failed'
            self.status_details = '[ERROR] File Already Exists: {}'.format(filename)
            return self.id_vpn_access_requests
        else:
            current_reused_ip = None
            result = self.get_reusable_ip()
            if result:
                current_reused_ip = result['ip_addr_1']
                next_ip_1 = result['ip_addr_1']
                next_ip_2 = result['ip_addr_2']
            else:
                try:
                    next_ip_1, next_ip_2 = self.get_ip_addr()
                except ValueError:
                    print(sys.exc_info())
                    self.status_details = '[ERROR] ValueError next_ip has no value.'
                    if '[FATAL] Vpn_Access' in str(sys.exc_info()):
                        self.status_details = '[FATAL]'
                    self.status = 'failed'
                    return self.id_vpn_access_requests

            if not self.add_file_to_ccd(self.account_filename, next_ip_1, next_ip_2):
                # return status_failed
                self.status = 'failed'
                self.status_details = '[ERROR] add_file_to_ccd.'
                return self.id_vpn_access_requests

            #RUN PKI-TOOL
            vpn_files = self.run_pkitool() or []
            if not vpn_files:
                self.status = 'failed'
                self.status_details = '[ERROR] vpn_files.'
                return self.id_vpn_access_requests

            #RUN GENERERATE_CONF_FILE
            conf_file = self.genererate_conf_file()
            if not conf_file:
                self.status = 'failed'
                self.status_details = '[ERROR] conf_file.'
                return self.id_vpn_access_requests

            #ZIP FILES
            self.zip_file_path = os.path.join(self.zipfiles_main_path, "{}.zip".\
                                         format(self.account_filename))

            vpn_files = vpn_files + [conf_file] # append doesn't work?
            if not self.zip_file(vpn_files, self.zip_file_path):
                print("[ERROR] zip file error.")
                self.status = 'failed'
                self.status_details = '[ERROR] zip file error.'
                return self.id_vpn_access_requests

            #ADD DATA IN ACCOUNT_VPN_ACCESS
            conditions = []
            data = {}
            print('id_vpn_access_requests:', self.id_vpn_access_requests)
            data['id_vpn_access_requests'] = self.id_vpn_access_requests
            data['ip_addr_1'] = next_ip_1
            data['ip_addr_2'] = next_ip_2
            data['vpn_type']  = self.vpn_type
            data['account_id'] = self.account_id
            data['zip_file_path'] = self.zip_file_path
            data['account_filename'] = self.account_filename
            data['is_active'] = 1
            data['last_update_date'] = datetime.fromtimestamp(time.time())

            if not self.postgresql_query.insert('account_vpn_access', data, 'account_id'):
                print("[ERROR] Unable to insert account_vpn_access table.")
                self.status = 'failed'
                self.status_details = '[ERROR] Unable to insert account_vpn_access table.'
                return self.id_vpn_access_requests

            # UPDATE CURRENT IP IN VPN_ACCESS TABLE
            conditions = []
            conditions.append({
                "col": "vpn_type",
                "con": "=",
                "val": self.vpn_type #"CLIENT",
                })
            data = {}
            if current_reused_ip:
                data['current_reused_ip'] = current_reused_ip
            else:
                data['current_ip_1'] = next_ip_1
                data['current_ip_2'] = next_ip_2
            data['update_on'] = datetime.fromtimestamp(time.time())

            if self.postgresql_query.update('vpn_access', data, conditions):
                if not self.delete_conf_file(conf_file):
                    print("[WARNING]: wasn't able to delete .conf file.")
                print('DONE: create_static_ip')

                # UPDATE CURRENT IP IN VPN_ACCESS TABLE
                conditions = []
                conditions.append({
                    "col": "id",
                    "con": "=",
                    "val": self.id_vpn_access_requests #"CLIENT",
                })
                data = {}
                data['status'] = 'DONE'
                data['request_finish_date'] = datetime.fromtimestamp(time.time())
                #update request table:
                self.postgresql_query.update('vpn_access_requests', data, conditions)

                # return status_ok
                self.status = 'ok'
                self.status_details = 'Successfull.'
                self.current_ip_1 = next_ip_1
                return self.id_vpn_access_requests
            else:
                print("[ERROR]: Unable to update vpn_access table.")
                # return status_failed
                self.status = 'failed'
                self.status_details = '[ERROR]: Unable to update vpn_access table.'
                return self.id_vpn_access_requests


    def add_file_to_ccd(self, filename, next_ip_1, next_ip_2):
        print("RUNNING - add_file_to_ccd.")
        os.chdir(self.ccd_path)

        content = 'ifconfig-push {} {}'.format(next_ip_1, next_ip_2)
        cmd = "echo '{}' > {filename}".format(content, filename=filename)
        os.system(cmd)

        #VALIDATE FILE
        if os.path.exists(filename):
            return True
        else:
            print('ERROR: {} in ccd/ is not created.'.format(filename))
            return False


    def run_pkitool(self):
        print("RUNNING - run_pkitool.")

        #CHANGING DIR IS REQUIRED TO RUN THE PROGRAM PROPERLY.
        os.chdir(self.easy_rsa_path)

        # RUN COMMAND
        cmd = '. ./vars  &&  ./pkitool {}'.format(self.account_filename)
        os.system(cmd)

        #CHANGE DIR
        os.chdir(self.easy_rsa_key_path)

        filename = os.path.join(self.easy_rsa_key_path, self.account_filename)
        extensions = ['key', 'crt']
        files_w_ext = ['{}.{}'.format(filename, ext) for ext in extensions]
        files_w_ext = files_w_ext + ['ca.crt']

        for file in files_w_ext:
            if not os.path.exists(file):
                print('ERROR: {} in keys/ is not created.'.format(file))
                return False
        return files_w_ext


    def genererate_conf_file(self):
        print('RUN: genererate_conf_file')
        try:
            with open(self.vpn_default_conf_path, 'r') as f:
                ext = ACCOUNT_OS[self.account_os]['conf_extension']
                file = os.path.join(self.easy_rsa_key_path, "{}.{}".format(self.account_filename, ext))
                with open(file, 'w') as f1:
                    content = str(f.read().format(ACCOUNT_NAME=self.account_filename))
                    f1.write(content)
                if os.path.exists(file):
                    return file
                return 0
        except:
            print(str(sys.exc_info()))
            return 0


    def delete_conf_file(self, conf_file_path):
        print("conf_file_path:", conf_file_path)
        os.system('rm {}'.format(conf_file_path))
        if not os.path.exists(conf_file_path):
            return 1
        return 0

    def get_reusable_ip(self):

        sql_str = """
                SELECT  DISTINCT ip_addr_1, ip_addr_2, id_vpn_access_requests FROM (
                    SELECT * FROM public.account_vpn_access
                        WHERE is_active = 0 AND vpn_type='{}' AND ip_addr_1 NOT IN(
                            SELECT ip_addr_1 FROM public.account_vpn_access WHERE vpn_type='{}' AND is_active = 1
                        )
                    ) AS q1
                    ORDER BY id_vpn_access_requests DESC LIMIT 1
            """.format(self.vpn_type, self.vpn_type)
        self.postgresql_query.connection()
        res = self.postgresql_query.query_fetch_one(sql_str)
        print('res:', res)
        self.postgresql_query.close_connection()
        return res

    def get_ip_addr(self):
        print("RUNNING - get_ip_addr.")
        self.postgresql_query.connection()

        next_ip_1 = None
        next_ip_2 = None

        # sql_str = "SELECT * FROM vpn_access WHERE vpn_type='CLIENT'"
        sql_str = "SELECT * FROM vpn_access WHERE vpn_type='{}'".format(self.vpn_type)
        res = self.postgresql_query.query_fetch_one(sql_str)

        assert res, 'VPN TYPE ({}) does not exists is not initialized in vpn_access.'.format(self.vpn_type)

        print('CURRENT IP:', res['current_ip_1'])
        print('CURRENT IP:', res['current_ip_2'])
        print('\n')

        current_ip_1 = res['current_ip_1']
        current_ip_2 = res['current_ip_2']

        # COMPUTE FOR NEXT-IP 
        while True:
            if next_ip_1:
                res['current_ip_1'] = next_ip_1
                res['current_ip_2'] = next_ip_2
            next_ip_1, next_ip_2 = self.compute_for_next_ip(res)

            # CHECK IF EXISTS IN DB
            sql_str = "SELECT * FROM account_vpn_access WHERE vpn_type='{}' AND ip_addr_1='{}' AND ip_addr_2='{}' AND is_active=1"\
                        .format(self.vpn_type, next_ip_1, next_ip_2)
            ip_exist = self.postgresql_query.query_fetch_one(sql_str)
            if not ip_exist:
                break

        print('NEXT IP:',next_ip_1)
        print('NEXT IP:',next_ip_2)
        print('\n')

        # CLOSE CONNECTION
        self.postgresql_query.close_connection()

        return next_ip_1, next_ip_2


    def compute_for_next_ip(self, res):
        print('''Computation for next ip for vpn.''')

        octet_1  = res.get('octet_1')

        octet_2_min  = res.get('octet_2_min')
        octet_3_min  = res.get('octet_3_min')
        octet_4_min  = res.get('octet_4_min')

        octet_2_max  = res.get('octet_2_max')
        octet_3_max  = res.get('octet_3_max')
        octet_4_max  = res.get('octet_4_max')

        ip = res.get('current_ip_1').split('.')
        current_octet_2 = int(ip[1])
        current_octet_3 = int(ip[2])
        current_octet_4 = int(ip[3])

        next_octet_2 = current_octet_2
        next_octet_3 = current_octet_3
        next_octet_4 = current_octet_4

        next_ip_1 = None
        next_ip_2 = None

        valid_numbers = {'1': 2, '5': 6, '9': 10, '13': 14, '17': 18, '21': 22,
                         '25': 26, '29': 30, '33': 34, '37': 38, '41': 42,
                         '45': 46, '49': 50, '53': 54, '57': 58, '61': 62,
                         '65': 66, '69': 70, '73': 74, '77': 78, '81': 82,
                         '85': 86, '89': 90, '93': 94, '97': 98, '101': 102,
                         '105': 106, '109': 110, '113': 114, '117': 118,
                         '121': 122, '125': 126, '129': 130, '133': 134,
                         '137': 138, '141': 142, '145': 146, '149': 150,
                         '153': 154, '157': 158, '161': 162, '165': 166,
                         '169': 170, '173': 174, '177': 178, '181': 182,
                         '185': 186, '189': 190, '193': 194, '197': 198,
                         '201': 202, '205': 206, '209': 210, '213': 214,
                         '217': 218, '221': 222, '225': 226, '229': 230,
                         '233': 234, '237': 238, '241': 242, '245': 246,
                         '249': 250, '253': 254}

        next_octet_4_1 = None
        next_octet_4_2 = None
        next_valid_num = str(current_octet_4 + 4)

        # GET FIRST IP
        if res.get('current_ip_1') == '0.0.0.0':
            next_octet_4_2 = valid_numbers.get('1')
            next_octet_4_1 = next_octet_4_2 - 1
            next_octet_2 = octet_2_min
            next_octet_3 = octet_3_min
        # GET NEXT-OCTET 4
        elif valid_numbers.get(next_valid_num, False):
            next_octet_4_2 = valid_numbers[str(next_valid_num)]
            next_octet_4_1 = next_octet_4_2 - 1
        # IF OCTET 4 EXCEEDS
        else:
            print('yyyyy')
            next_octet_4_1 = octet_4_min
            next_octet_4_2 = next_octet_4_1 + 1
            if (current_octet_3+1) <= octet_3_max:
                next_octet_3 = current_octet_3 + 1
            # IF OCTET 3 EXCEEDS
            else:
                next_octet_3 = octet_3_min
                # IF OCTET 2 EXCEEDS
                if current_octet_2+1 <= octet_2_max:
                    next_octet_2 = current_octet_2 + 1
                # REACHED MAXIMUM VPN_ACCESS
                else:
                    raise ValueError("[FATAL] Vpn_Access For Account-Type: {} Has"\
                                     " Reached It's Limit".format(self.vpn_type))


        next_ip_1 = "{}.{}.{}.{}".format(octet_1, next_octet_2,\
                                        next_octet_3, next_octet_4_1)
        next_ip_2 = "{}.{}.{}.{}".format(octet_1, next_octet_2,\
                                        next_octet_3, next_octet_4_2)

        return next_ip_1, next_ip_2


    def zip_file(self, file_paths, zip_file_path):
        '''file paths should be absolute'''
        print('RUN: zip_file')
        for file in file_paths:
            if not os.path.exists(file):
                print("[ERROR] File {} doesn't exist".format(file))
                return False

        files = ' '.join(file_paths)
        cmd = 'zip -rj {} {}'.format(zip_file_path, files)
        os.system(cmd)

        if os.path.exists(zip_file_path):
            return True
        return False

class Vpn_Access_Create_AllowDisallowed:

    openvpn_path           = '/etc/openvpn'
    # crt_file_path           = 'SAMPLE_CRT_FILE.crt'

    def __init__(self,
                 id_vpn_access_requests,
                 account_id,
                 account_vpn_ip,

                 web_prod_ip_address = '10.1.1.1' ,
                 web_prod_ip_port=22,
                 web_prod_username='gbf',
                 web_prod_password='#Gl0Bal&BrAinF',
                 web_prod_config_file='webprod.conf',

                 api_prod_ip_address = '10.8.2.9',
                 api_prod_ip_port=22,
                 api_prod_username='gbf',
                 api_prod_password='#Gl0Bal&BrAinF',
                 api_prod_config_file='apiprod.conf',

                 # web_prod_ip_address = '172.18.0.4' ,
                 # web_prod_ip_port=22,
                 # web_prod_username='root',
                 # web_prod_password='1234',
                 # web_prod_config_file='SAMPLE_CRT_FILE.crt',

                 # api_prod_ip_address = '172.18.0.3',
                 # api_prod_ip_port=22,
                 # api_prod_username='root',
                 # api_prod_password='1234',
                 # api_prod_config_file='SAMPLE_CRT_FILE.crt',

                 # web_prod_ip_address,
                 # web_prod_ip_port,
                 # web_prod_username,
                 # web_prod_password,
                 # web_prod_config_file,

                 # api_prod_ip_address,
                 # api_prod_ip_port,
                 # api_prod_username,
                 # api_prod_password,
                 # api_prod_config_file
        ):
        print('[Vpn_Access_Create_AllowDisallowed]:')

        self.server_list = [
            {
                 'name': 'web_prod'
                ,'ip_addr': web_prod_ip_address
                ,'ip_port': web_prod_ip_port
                ,'username': web_prod_username
                ,'password': web_prod_password
                ,'config_file': web_prod_config_file
            },
            {
                 'name': 'api_prod'
                ,'ip_addr': api_prod_ip_address
                ,'ip_port': api_prod_ip_port
                ,'username': api_prod_username
                ,'password': api_prod_password
                ,'config_file': api_prod_config_file
            },
        ]
        #DEBUG
        # self.server_list = [self.server_list[0]]
        #DEBUG

        self.id_vpn_access_requests = id_vpn_access_requests
        self.account_id = account_id
        self.account_vpn_ip = account_vpn_ip

        self.is_ssh_connection_error = 0
        self.postgresql_query = PostgreSQL()

    def add_access(self):
        print("[START] - add_access.")

        status = '' # ok | failed
        status_details = []

        data = {}
        data['id_vpn_access_requests'] = self.id_vpn_access_requests
        data['request_type'] = 'add-access'
        data['account_id'] = self.account_id
        data['account_vpn_ip'] = self.account_vpn_ip
        data['is_active'] = 0
        data['request_finish_date'] = datetime.fromtimestamp(time.time())
        self.postgresql_query.connection()
        is_created = self.postgresql_query.insert('account_vpn_access_webprod_apiprod', data, table_id='1')
        self.postgresql_query.close_connection()


        # START PROCESSING
        for server_data in self.server_list:

            ssh_server = SSH_Server(
                 server_ip = server_data['ip_addr']
                ,port = server_data['ip_port']
                ,username = server_data['username']
                ,password = server_data['password']
            )
            ssh_server.ssh_to_server()

            if ssh_server.connection_error:
                status_details.append(ssh_server.connection_error)
                status = 'failed'
                self.is_ssh_connection_error = 1
            else:
                command_checker = ' && '.join([
                    "cd {}".format(Vpn_Access_Create_AllowDisallowed.openvpn_path)
                    ,"cat {}".format(server_data['config_file'])
                ])
                stdout, stderr = ssh_server.run_command(command_checker)

                if self.account_vpn_ip in stdout:
                    status_details.append('IP {} is already in Server {}'.format(self.account_vpn_ip, server_data['ip_addr']))
                    status = 'ok' # status = 'failed'
                else:
                    content = 'route {}'.format(self.account_vpn_ip)
                    append_content = "echo '{}' >> {}".format(content, server_data['config_file'])
                    commands = [
                        "cd {}".format(Vpn_Access_Create_AllowDisallowed.openvpn_path)
                        ,append_content
                        ,"cat {}".format(server_data['config_file'])
                    ]

                    command = ' && '.join(commands)
                    print('command: ', command)

                    stdout, stderr = ssh_server.run_command(command)

                    #CHECK IP IN THE OUTPUT
                    if self.account_vpn_ip in stdout:
                        status_details.append('Successfull adding IP to Vessel {}'.format(server_data['ip_addr']))
                        status = 'ok'
                        #RESTART OPENVPN SERVER
                        command_restart = "sudo service openvpn restart"
                        if server_data['username'] == 'root':
                            command_restart = "service openvpn restart"
                        ssh_server.run_command(command_restart)
                    else:
                        status_details.append('Not able to add Ip to Vessel: {}'.format(server_data['ip_addr']))
                        status = 'failed'

        # UPDATE Account_vpn_access_webprod_apiprod
        conditions = []
        conditions.append({
            "col": "id_vpn_access_requests",
            "con": "=",
            "val": self.id_vpn_access_requests
        })
        data = {}
        data['status'] = status
        data['status_details'] = ' | '.join(status_details)
        data['request_finish_date'] = datetime.fromtimestamp(time.time())
        self.postgresql_query.update('account_vpn_access_webprod_apiprod', data, conditions)

        print("[END] - add_access.")

    def remove_access(self):
        print("[START] - remove_access.")

        status = '' # ok | failed
        status_details = []

        data = {}
        data['id_vpn_access_requests'] = self.id_vpn_access_requests
        data['request_type'] = 'remove-access'
        data['account_id'] = self.account_id
        data['account_vpn_ip'] = self.account_vpn_ip
        data['is_active'] = 0
        data['request_finish_date'] = datetime.fromtimestamp(time.time())
        self.postgresql_query.connection()
        is_created = self.postgresql_query.insert('account_vpn_access_webprod_apiprod', data, table_id='1')
        self.postgresql_query.close_connection()

        # START PROCESSING
        for server_data in self.server_list:

            ssh_server = SSH_Server(
                 server_ip = server_data['ip_addr']
                ,port = server_data['ip_port']
                ,username = server_data['username']
                ,password = server_data['password']
            )
            ssh_server.ssh_to_server()

            if ssh_server.connection_error:
                status_details.append(ssh_server.connection_error)
                status = 'failed'
                self.is_ssh_connection_error = 1
            else:
                command_checker = ' && '.join([
                    "cd {}".format(Vpn_Access_Create_AllowDisallowed.openvpn_path)
                    ,"cat {}".format(server_data['config_file'])
                ])
                stdout, stderr = ssh_server.run_command(command_checker)

                if self.account_vpn_ip not in stdout:
                    status = 'ok' # status = 'failed'
                    status_details.append('IP {} is not present in Server {}'.format(self.account_vpn_ip, server_data['ip_addr']))
                    print(status_details)
                else:
                    content = 'route {}'.format(self.account_vpn_ip)
                    append_content = "sudo sed -i '/{}/d' {}".format(content, server_data['config_file'])
                    commands = [
                        "cd {}".format(Vpn_Access_Create_AllowDisallowed.openvpn_path)
                        ,append_content
                        ,"cat {}".format(server_data['config_file'])
                    ]

                    command = ' && '.join(commands)
                    print('command: ', command)

                    stdout, stderr = ssh_server.run_command(command)
                    #CHECK IP IN THE OUTPUT
                    if self.account_vpn_ip not in stdout:
                        status_details.append('Successfull removing IP to Server {}'.format(server_data['ip_addr']))
                        status = 'ok'
                        #RESTART OPENVPN SERVER
                        command_restart = "sudo service openvpn restart"
                        if server_data['username'] == 'root':
                            command_restart = "service openvpn restart"
                        ssh_server.run_command(command_restart)
                    else:
                        status = 'failed'
                        status_details.append('Not able to add Ip to Server: {}'.format(server_data['ip_addr']))
                        print(status_details)

        # UPDATE Account_vpn_access_webprod_apiprod
        conditions = []
        conditions.append({
            "col": "id_vpn_access_requests",
            "con": "=",
            "val": self.id_vpn_access_requests
        })
        data = {}
        data['status'] = status
        data['status_details'] = ' | '.join(status_details)
        data['request_finish_date'] = datetime.fromtimestamp(time.time())
        self.postgresql_query.update('account_vpn_access_webprod_apiprod', data, conditions)

        print("[END] - remove_access.")

class Vpn_Access_Revoke:

    ccd_path           = '/etc/openvpn/ccd'
    easy_rsa_path      = '/etc/openvpn/easy-rsa/'
    easy_rsa_key_path  = '/etc/openvpn/easy-rsa/keys/'
    zipfiles_main_path = '/home/'

    def __init__(self, id_vpn_access_requests, account_id, vpn_type):
        self.account_id = account_id
        self.vpn_type = vpn_type
        self.account_filename = None
        self.id_account_vpn_access = None
        self.id_vpn_access_requests = id_vpn_access_requests

        self.default_data_status = ''
        self.status = ''
        self.status_details = ''

        self.postgresql_query = PostgreSQL()
        self._set_default_data()


    def _set_default_data(self):
        print("START - _set_default_data.")

        try:
            self.postgresql_query.connection()
            sql_str = "SELECT id_vpn_access_requests, account_filename FROM account_vpn_access WHERE account_id={} AND vpn_type='{}' AND is_active=1".\
                format(self.account_id, self.vpn_type)
            result = self.postgresql_query.query_fetch_one(sql_str)
            # print('--'*100)
            # print('result:', result)
            if hasattr(result, 'get'):
                self.account_filename = result.get('account_filename', None)
                self.id_account_vpn_access = result.get('id_vpn_access_requests', None)
            else:
                raise ValueError('No Data Found in account_vpn_access.')
        except:
            if self.account_filename == None:
                self.default_data_status = 'failed'
                self.default_status_details = 'Account_ID {} has no active vpn for vpn_type={}'.format(self.account_id, self.vpn_type)
            print(str(self.default_status_details))
        finally:
            print('-'*100)
            print('id_account_vpn_access:', self.id_account_vpn_access)
            print('account_filename:', self.account_filename)
            self.postgresql_query.close_connection()

        print("END - _set_default_data.")


    def revoke(self):
        '''
            PROCESS:
                source vars
                ./revoke-full <file-name>
                rm the filename in ccd
        '''
        print("RUNNING - revoke.")

        if self.default_data_status == 'failed':
            self.status = 'DENIED'
            self.status_details = self.default_status_details
        else:
            try:
                #CHANGING DIR IS REQUIRED TO RUN THE PROGRAM PROPERLY.
                os.chdir(self.easy_rsa_path)

                #RUN COMMAND
                cmd = '. ./vars  &&  ./revoke-full {} && service openvpn restart'.format(self.account_filename)
                os.system(cmd)

                #REMOVE FILE IN CCD
                os.chdir(self.ccd_path)
                cmd = 'rm {}'.format(self.account_filename)
                os.system(cmd)

                self.status = 'DONE'
            except:
                self.status = 'DENIED'
                self.status_details = 'ERROR: '.format(str(sys.exc_info()))

            print('\n'*2)
            print('status:', self.status)
            print('self.id_vpn_access_requests', self.id_vpn_access_requests)
            if self.status == 'DONE':
                #MARK ACCOUNT_VPN_ACCESS
                conditions = []
                conditions.append({
                    "col": "id_vpn_access_requests",
                    "con": "=",
                    "val": self.id_account_vpn_access #"CLIENT",
                })
                data = {}
                data['is_active'] = 0
                data['last_update_date'] = datetime.fromtimestamp(time.time())
                self.postgresql_query.update('account_vpn_access', data, conditions)

        # UPDATE CURRENT IP IN VPN_ACCESS TABLE
        conditions = []
        conditions.append({
            "col": "id",
            "con": "=",
            "val": self.id_vpn_access_requests
        })
        data = {}
        data['status'] = self.status
        data['status_details'] = self.status_details
        data['request_finish_date'] = datetime.fromtimestamp(time.time())
        self.postgresql_query.update('vpn_access_requests', data, conditions)

        print("DONE - revoke.")

def vpn_terminal_receiver():

    '''
        eg. terminal command:

            python vpn_access.py -job_id 2 -callback_url https://www.google.com -data_url https://www.google.com -token fsdlkfsa349543054305

                eg.
                    python vpn_access.py -job_id 2 -callback_url https://www.google.com -data_url https://www.fb.com -token fsdlkfsa349543054305

                EXPECTED DATA FROM -data_url:

                    data = {
                        "vessel_ips": [
                                    {
                                      'ip': '127.0.0.1'
                                     ,'port': '22'
                                     ,'username': 'username'
                                     ,'password': 'password'
                                     ,'vessel_name': 'name of vessel'
                                     }
                                ],
                        "account_id": 1,
                        "account_ip_address": '127.0.0.1', #VESSEL VPN
                        "account_name": "rh",
                        "vpn_type": "VESSEL",
                        "account_os": "LINUX",
                        "action": "DELETE"
                    }

            Actions for users VPN:
                Create [DONE]
                Delete [DONE]

            Actions for Vessels VPN:
                Create [DONE]
                Delete [DONE]
                Add [DONE]
                Remove [DONE]
    '''

    print('***[START] vpn_terminal_receiver.')

    parser = argparse.ArgumentParser()

    parser.add_argument('-job_id', action='store', dest='job_id',
                        help='Job ID')
    parser.add_argument('-callback_url', action='store', dest='callback_url',
                        help='Operating System')
    parser.add_argument('-data_url', action='store', dest='data_url',
                        help='Data Url')
    parser.add_argument('-token', action='store', dest='token',
                        help='Request Token')

    results = parser.parse_args()

    job_id = int(results.job_id)
    callback_url = results.callback_url
    data_url = results.data_url
    token = results.token

    data = []

    if True:
        try: #PRODUCTION
            headers = {'content-type': 'application/json', 'token': str(token), 'jobid': str(job_id)}
            r = requests.get(data_url, headers=headers)
            res = r.json()
            if res['status'] == 'ok':
                data = res['data']
        except:
            print("token: ", token)
            print("job_id: ", job_id)
            print("data_url: ", data_url)
            print("Invalid data!")
            sys.exit(0)

    vessel_ips = data['vessel_ips']
    account_id = data['account_id']
    account_ip_address = data['account_ip_address']
    account_name = data['account_name']
    vpn_type = data['vpn_type']
    account_os = data['account_os']
    action = data['action'].upper()
    vpn_request_type = action
    print("vessel_ips: ", vessel_ips)
    if vpn_type in ['CLIENT', 'GBF', 'RH', 'UNKNOWN']:

        if action in ['CREATE', 'DELETE']:
            vpn_access = Vpn_Access_Main(job_id, callback_url, token, account_id, vpn_type, vpn_request_type, account_name, account_os)
            vpn_access.run()
        else:
            raise ValueError('Invalid Request Action ({} - {})'.format(vpn_type, action))

    elif vpn_type in ['VESSEL', 'VCLIENT', 'VGBF', 'VRH', 'VUNKNOWN']:

        if action in ['CREATE', 'DELETE']:
            vpn_access = Vpn_Access_Main(
                job_id = job_id,
                callback_url = callback_url,
                token = token,
                account_id = account_id,
                account_name = account_name,
                vpn_type = vpn_type,
                vpn_request_type = vpn_request_type,
                account_os = account_os)
            vpn_access.run()
            os.system('sudo service openvpn restart')

        elif action == 'ADD':
            print('''Real Vessel - ADD''')
            for real_vessel in vessel_ips:
                vpn_real = Vpn_Access_RealVessel(
                     vessel_ip_address = real_vessel['ip']
                    ,vessel_name = real_vessel['vessel_name']
                    ,vessel_username = real_vessel['username']
                    ,vessel_password = real_vessel['password']
                    ,vessel_port = real_vessel['port']
                    ,vessel_imo = real_vessel['imo']
                    ,account_id = account_id
                    ,account_ip_address = account_ip_address
                    ,token = token
                    ,job_id = job_id
                    ,callback_url = callback_url
                    ,vpn_type = vpn_type
                )
                if vpn_real.self_check_status:
                    vpn_real.add_access()
            #os.system('sudo service openvpn restart')

        elif action == 'REMOVE':
            print('''Real Vessel - REMOVE''')
            for real_vessel in vessel_ips:
                vpn_real = Vpn_Access_RealVessel(
                     vessel_ip_address = real_vessel['ip']
                    ,vessel_name = real_vessel['vessel_name']
                    ,vessel_username = real_vessel['username']
                    ,vessel_password = real_vessel['password']
                    ,vessel_port = real_vessel['port']
                    ,vessel_imo = real_vessel['imo']
                    ,account_id = account_id
                    ,account_ip_address = account_ip_address
                    ,token = token
                    ,job_id = job_id
                    ,callback_url = callback_url
                    ,vpn_type = vpn_type
                    ,action = 'REMOVE'
                )
                if vpn_real.self_check_status:
                    vpn_real.remove_access()
            #os.system('sudo service openvpn restart')

        else:
            raise ValueError('Invalid Request Action ({} - {})'.format(vpn_type, action))


if __name__  == '__main__':

    vpn_terminal_receiver()
