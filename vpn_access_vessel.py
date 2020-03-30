import os
import sys
import subprocess
from library.postgresql_queries import PostgreSQL
from datetime import datetime
import time
import paramiko
from vpn_access import Vpn_Access_Main
from scp import SCPClient


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


class Vpn_Access:

    ccd_path           = '/etc/openvpn/ccd'
    easy_rsa_path      = '/etc/openvpn/easy-rsa/'
    easy_rsa_key_path  = '/etc/openvpn/easy-rsa/keys/'
    zipfiles_main_path = '/home/'

    def __init__(self, id_vpn_access_requests, account_id, account_name, vpn_type, account_os):

        self.id_vpn_access_requests = id_vpn_access_requests
        self.account_id       = account_id
        self.account_name     = account_name
        self.vpn_type         = vpn_type
        self.account_os       = account_os
        self.postgresql_query = PostgreSQL()

        self.conf_default_root_path  = os.getcwd() #os.path.join(os.getcwd(), 'WEB_API_VPN_DEFAULT_CONFIGURATION_FILE')
        self.account_filename   = Vpn_Access.set_account_filename(vpn_type, account_id, account_name)
        self.current_ip_1 = None
        self.current_ip_2 = None

        self.self_check_status = True
        self.self_check()

        #DEBUG:
        # time.sleep(5)


    @property
    def vpn_default_conf_path(self):
        '''Configuration files and vpn_access.py should be in the same folder.'''

        self.postgresql_query.connection()
        sql_str = "SELECT config_file_name FROM vpn_access WHERE vpn_type = '{}' ".format(self.vpn_type)
        config_file_name = self.postgresql_query.query_fetch_one(sql_str)
        self.postgresql_query.close_connection()

        config_file_name = config_file_name['config_file_name']

        if config_file_name:
            return os.path.join(self.conf_default_root_path, config_file_name)
        else:
             raise ValueError('[ERROR] Unknown Account Type.')


    @staticmethod
    def set_account_filename(vpn_type, account_id, account_name):
        account_filename   = '{}_{:02d}_{}'.format(vpn_type, account_id, account_name)
        print('account_filename:', account_filename)
        return account_filename


    def self_check(self):
        '''CHECKING ALL CAUSES OF POSSIBLE ERRORS.'''

        #VERIFY IF THE USER DOESN'T HAVE EXISTING VPN THAT IS ACTIVE
        self.postgresql_query.connection()
        sql_str = "SELECT COUNT(1) FROM account_vpn_access WHERE account_id={} AND vpn_type='{}'".\
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
            assert self.vpn_default_conf_path
            assert os.path.exists(self.ccd_path)
            assert os.path.exists(self.easy_rsa_path)
            assert os.path.exists(self.easy_rsa_key_path)
            assert os.path.exists(self.zipfiles_main_path)

            assert not os.path.exists(os.path.join(self.ccd_path, self.account_filename)), 'Existing file in ccd.'

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
            # status_failed = 'failed'
            return self.id_vpn_access_requests

        self.postgresql_query.connection()
        sql_str = "SELECT COUNT(1) FROM vpn_access where vpn_type ='{}'".format(self.vpn_type)
        count = self.postgresql_query.query_fetch_one(sql_str)
        is_exists = count['count']
        self.postgresql_query.close_connection()

        if not is_exists:
            print("[ERROR] Account type {} doesn't exists.".format(self.vpn_type))
            # return status_failed
            return self.id_vpn_access_requests

        filename = os.path.join(self.ccd_path, self.account_filename)

        if os.path.exists(filename):
            print('[ERROR] File Already Exists: {}'.format(filename))
            # return status_failed
            return self.id_vpn_access_requests
        else:
            try:
                next_ip_1, next_ip_2 = self.get_ip_addr()
            except ValueError:
                print(sys.exc_info())
                if '[FATAL] Vpn_Access' in str(sys.exc_info()):
                    return 'failed'
                # return status_failed
                return self.id_vpn_access_requests

            if not self.add_file_to_ccd(self.account_filename, next_ip_1, next_ip_2):
                # return status_failed
                return self.id_vpn_access_requests

            #RUN PKI-TOOL
            vpn_files = self.run_pkitool() or []
            if not vpn_files:
                # return status_failed
                return self.id_vpn_access_requests

            #RUN GENERERATE_CONF_FILE
            conf_file = self.genererate_conf_file()
            if not conf_file:
                # return status_failed
                return self.id_vpn_access_requests

            #ZIP FILES
            zip_file_path = os.path.join(self.zipfiles_main_path, "{}.zip".\
                                         format(self.account_filename))

            vpn_files = vpn_files + [conf_file] # append doesn't work?
            if not self.zip_file(vpn_files, zip_file_path):
                print("[ERROR] zip file error.")
                # return status_failed
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
            data['zip_file_path'] = zip_file_path

            if not self.postgresql_query.insert('account_vpn_access', data, 'account_id'):
                print("[ERROR] Unable to update account_vpn_access table.")
                # return status_failed
                return self.id_vpn_access_requests

            # UPDATE CURRENT IP IN VPN_ACCESS TABLE
            conditions = []
            conditions.append({
                "col": "vpn_type",
                "con": "=",
                "val": self.vpn_type #"CLIENT",
                })
            data = {}
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
                data['status'] = 'FINISHED-VS'
                data['request_finish_date'] = datetime.fromtimestamp(time.time())
                #update request table:
                self.postgresql_query.update('vpn_access_requests', data, conditions)

                # return status_ok
                return self.id_vpn_access_requests

            else:
                print("[ERROR]: Unable to update vpn_access table.")
                # return status_failed
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

        #COMPUTE FOR NEXT-IP
        next_ip_1, next_ip_2 = self.compute_for_next_ip(res)

        print('NEXT IP:',next_ip_1)
        print('NEXT IP:',next_ip_2)
        print('\n')

        # CLOSE CONNECTION
        self.postgresql_query.close_connection()

        return next_ip_1, next_ip_2


    def compute_for_next_ip(self, res):
        '''Computation for next ip for vpn.'''

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


class SSH_Vessel_Main_SCP:

    def __init__(self, account_filename):
        self.web_server_ip = '172.18.0.3'
        self.port = 22
        self.username = 'root'
        self.password = '1234'
        self.ssh_client = None

        self.account_filename = account_filename
        # self.postgresql_query = PostgreSQL()

    def ssh_to_server(self):
        print('[START] another_init:')
        self.ssh_client = paramiko.SSHClient()                                   # create SSHClient instance
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())    # AutoAddPolicy automatically adding the hostname and new host key
        self.ssh_client.load_system_host_keys()
        try:
            self.ssh_client.connect(self.web_server_ip, self.port, self.username, self.password)
        except paramiko.ssh_exception.SSHException as e:
            print('IP: {} not found in known_hosts.'.format(self.web_server_ip))
            raise e
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            print('Cannot connect to IP: {}'.format(self.web_server_ip))
            raise e

    def scp_file(self):
        print('[START] scp_file:')
        print('file_source_path:', self.account_filename)
        file_source_path = self.account_filename
        # time.sleep(3)
        with SCPClient(self.ssh_client.get_transport()) as scp:
            with open(self.account_filename, 'rb') as file:
                scp.putfo(file, file_source_path)

            # print(dir(scp))
            # scp.put(file_source_path, file_source_path)
            # scp.get(file_source_path, file_source_path)
        print('[DONE] scp_file:')


def vpn_terminal_receiver():
    '''
        CURRENTLY-ONLY-THE-VESSEL-VPN-CAN-USE-THIS

        example terminal command:
            python vpn_access_vessel.py -action add-vessel-via-ssh-connection -account-id 22\
                -account-name kelly -vpn-type VESSEL -account-os LINUX
    '''
    print('***[START] vpn_terminal_receiver.')
    # print('sleeping....')
    # time.sleep(10)

    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument('-action', action='store', dest='action',
                        help='Vessel Action.')

    parser.add_argument('-id_vpn_access_requests', action='store', dest='id_vpn_access_requests',
                        help='Vpn access requests id.')

    parser.add_argument('-account-id', action='store', dest='account_id',
                        help='Account ID')

    parser.add_argument('-account-name', action='store', dest='account_name',
                        help='Account Name')

    parser.add_argument('-vpn-type', action='store', dest='vpn_type',
                        help='VPN Access Type')

    parser.add_argument('-account-os', action='store', dest='account_os',
                        help='Operating System')

    results = parser.parse_args()

    if results.action == 'add-vessel-via-ssh-connection':
        print(results.action)
        print(results.id_vpn_access_requests)
        print(results.account_id)
        print(results.account_name)
        print(results.vpn_type)
        print(results.account_os)

        account_id = int(results.account_id)
        id_vpn_access_requests = results.id_vpn_access_requests
        account_name = results.account_name
        vpn_type = results.vpn_type
        account_os = results.account_os

        vpn_access = Vpn_Access(id_vpn_access_requests, account_id, account_name, vpn_type, account_os)

        #SCP FILE AFTER COMMAND - create_static_ip
        print('*'*100)
        account_filename = os.path.join(Vpn_Access.zipfiles_main_path, Vpn_Access.set_account_filename(vpn_type, account_id, account_name))
        account_filename += '.zip'
        vpn_access_scp = SSH_Vessel_Main_SCP(
            account_filename=account_filename
        )
        #TEST SSH CONNECTION FIRST
        try:
            vpn_access_scp.ssh_to_server()
        except:
            conditions = []
            conditions.append({
                "col": "id",
                "con": "=",
                "val": id_vpn_access_requests
            })
            data = {}
            data['status'] = 'CONN-ERR'
            data['status_details'] = 'ERR: {} - {}'.format(vpn_access_scp.web_server_ip, str(sys.exc_info())[:401].replace('\'', '\"'))
            data['request_finish_date'] = datetime.fromtimestamp(time.time())
            vpn_access.postgresql_query.update('vpn_access_requests', data, conditions)
            return False


        ##### RUN COMMAND - create_static_ip
        vpn_access.create_static_ip()


        #SCP FILE
        try:
            vpn_access_scp.scp_file()
            vpn_access_scp.ssh_client.close()
        except:
            conditions = []
            conditions.append({
                "col": "id",
                "con": "=",
                "val": id_vpn_access_requests
            })
            data = {}
            data['status'] = 'CONN-ERR'
            data['status_details'] = 'ERR: {} - {}'.format(vpn_access_scp.web_server_ip, str(sys.exc_info())[:401].replace('\'', '\"'))
            data['request_finish_date'] = datetime.fromtimestamp(time.time())
            vpn_access.postgresql_query.update('vpn_access_requests', data, conditions)

        print('-'*100)

    else:
        print('[ERROR] Invalid Arguments.')

    print('***[END] vpn_terminal_receiver.')

