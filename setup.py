import time
import os
from configparser import ConfigParser

from library.config_parser import configSectionParser
from library.postgresql_queries import PostgreSQL
from library.sha_security import ShaSecurity


class Setup():

    def __init__(self):
        self.sha_security = ShaSecurity()
        self.postgres = PostgreSQL()

        # INIT CONFIG
        self.config = ConfigParser()
        # CONFIG FILE
        self.config.read("config/config.cfg")

    def main(self):

        self.create_database()
        self.create_tables()
        self.create_default_entries()

    def create_database(self):

        self.dbname = configSectionParser(self.config,"POSTGRES")['db_name']
        self.postgres.connection(True)
        self.postgres.create_database(self.dbname)
        self.postgres.close_connection()

    def create_tables(self):

        # OPEN CONNECTION
        self.postgres.connection()

        # VPN-ACCESS - CONFIG-FILE
        query_str = """
                CREATE TABLE public.vpn_access_conf_file (
                    config_file_name varchar(200) NOT null unique
                );
            """
        print("Create table: vpn_access_conf_file")
        if self.postgres.exec_query(query_str):
            print("Account VPN Access table successfully created!")

        # VPN-ACCESS
        query_str = """
                    CREATE TABLE public.vpn_access(
                        vpn_type varchar(16) NOT NULL,
                        prefix varchar(4) NOT null,
	                    config_file_name varchar(200) NOT null,
                        octet_1 int4 NOT NULL,
                        octet_2_min int4 NOT NULL,
                        octet_2_max int4 NOT NULL,
                        octet_3_min int4 NOT NULL,
                        octet_3_max int4 NOT NULL,
                        octet_4_min int4 NOT NULL,
                        octet_4_max int4 NOT NULL,
                        current_ip_1 varchar(16) NOT NULL DEFAULT '0.0.0.0',
                        current_ip_2 varchar(16) NOT NULL DEFAULT '0.0.0.0',
                        current_reused_ip varchar(16) NOT NULL DEFAULT '0.0.0.0',
                        update_on timestamp NULL,
                        CONSTRAINT vpn_access_type_pkey PRIMARY KEY (vpn_type),
                        CONSTRAINT vpn_access_vpn_type_key UNIQUE (vpn_type),
	                    CONSTRAINT account_vpn_access_conf_file_fkey FOREIGN KEY (config_file_name) REFERENCES vpn_access_conf_file(config_file_name) ON UPDATE CASCADE
                    );
                   """
        print("Create table: vpn_access")
        if self.postgres.exec_query(query_str):
            print("VPN Access table successfully created!")

        # VPN-ACCESS-REQUESTS-STATUS
        query_str = """
                CREATE TABLE public.vpn_access_requests_status (
                    id serial NOT NULL,
                    status varchar(16) NOT NULL,
                    description varchar(200) NULL,
                    CONSTRAINT vpn_access_requests_status_status_key UNIQUE (status)
                );
            """

        print("Create table: vpn_access_requests_status")
        if self.postgres.exec_query(query_str):
            print("VPN Access Requests Status table successfully created!")

        # VPN-ACCESS-REQUESTS
        query_str = """
                CREATE TABLE public.vpn_access_requests (
                    id serial NOT NULL,
	                job_id int8 NULL UNIQUE,
                    vpn_type varchar(16) NULL,          -- NULL BECAUSE OF MANUAL INSERT
                    vpn_request_type varchar(16) NULL,  -- NULL BECAUSE OF MANUAL INSERT
                    account_id int8 NOT NULL,           -- NULL BECAUSE OF MANUAL INSERT
                    account_name varchar(80) NULL,
                    account_os varchar(40) NULL,
                    request_start_date timestamp DEFAULT CURRENT_TIMESTAMP,
                    request_finish_date timestamp NULL,
                    status varchar(20) NOT NULL DEFAULT 'INITIALIZED'::character varying,
	                status_details varchar(400) NULL,
	                callback_status int NULL,
                    CONSTRAINT vpn_access_requests_id_key UNIQUE (id),
                    CONSTRAINT vpn_access_requests_status FOREIGN KEY (status) REFERENCES vpn_access_requests_status(status) ON UPDATE cascade 
                );
            """
        print("Create table: vpn_access_requests")
        if self.postgres.exec_query(query_str):
            print("VPN Access Requests table successfully created!")

        # ACCOUNT-VPN-ACCESS 
        query_str = """
                CREATE TABLE public.account_vpn_access(
            		id_vpn_access_requests int8,
                    ip_addr_1 varchar(16) NOT NULL,
                    ip_addr_2 varchar(16) NOT NULL,
                    vpn_type varchar(16) NOT NULL,
                    account_id int8 NULL, -- NULL BECAUSE OF MANUAL INSERT
                    zip_file_path varchar(200) NULL,
                    is_active int2 NULL,
                    last_update_date timestamp NULL,
                    account_filename varchar(200) NULL,
                    manually_added int2 NULL DEFAULT 0,
                    date_created timestamp default CURRENT_TIMESTAMP,
                    --CONSTRAINT account_vpn_access_pkey PRIMARY KEY (vpn_type, account_id, id_vpn_access_requests),
	                CONSTRAINT account_vpn_access_request_id_fkey FOREIGN KEY (id_vpn_access_requests) REFERENCES vpn_access_requests(id) ON UPDATE CASCADE ON DELETE CASCADE,
                    CONSTRAINT account_vpn_access_vpn_type_fkey FOREIGN KEY (vpn_type) REFERENCES vpn_access(vpn_type) ON UPDATE CASCADE ON DELETE CASCADE
                );
            """
        print("Create table: account_vpn_access")
        if self.postgres.exec_query(query_str):
            print("Account VPN Access table successfully created!")


        # ACCOUNT-VPN-ACCESS WEBPROD-APIPROD
        query_str = """
                CREATE TABLE public.account_vpn_access_webprod_apiprod (
                    id serial NOT NULL,
                    id_vpn_access_requests int8 NULL,
                    request_type varchar(20) NOT NULL,
                    account_id int8 NOT NULL,
                    account_vpn_ip varchar(15) NOT NULL,
                    is_active int4 NOT NULL,
                    status varchar(20) NULL,
                    status_details varchar(400) NULL,
                    request_finish_date timestamp NOT NULL,
                    CONSTRAINT account_vpn_access_webprod_apiprod_request_id_fkey FOREIGN KEY (id_vpn_access_requests) REFERENCES vpn_access_requests(id) ON UPDATE CASCADE ON DELETE CASCADE
                );
            """
        print("Create table: account_vpn_access_webprod_apiprod")
        if self.postgres.exec_query(query_str):
            print("Account VPN Access(WEBPROD-APIPROD) table successfully created!")


        #VPN_ACCESS_REAL_VESSEL_REQUESTS
        query_str = """
			CREATE TABLE public.vpn_access_real_vessel_requests (
                    id serial NOT NULL,
                    request_type varchar(40) NULL,
                    job_id int8 UNIQUE NOT NULL,

                    vessel_ip_address varchar(15) NOT NULL,
                    vessel_port varchar(80) NOT NULL,
                    vessel_username varchar(80) NOT NULL,
                    vessel_password varchar(80) NOT NULL,
                    token varchar(400) NOT NULL,
                    callback_url varchar(400) NULL,

                    account_id int8 NOT NULL,
                    account_vpn_ip varchar(15) NOT NULL,

                    request_start_date timestamp NOT NULL,
                    request_finish_date timestamp NULL,
                    status varchar(20) NULL,
                    status_details varchar(400) NULL,
                    callback_status int4 NULL,
                    is_ssh_connection_error int2 DEFAULT 0,
                    request_tries int2 DEFAULT 0,
                    CONSTRAINT vpn_access_real_vessel_requests_id_key UNIQUE (id)
                    --CONSTRAINT vpn_access_real_vessel_requests_job_id_key UNIQUE (job_id)
                );
            """
        print("Create table: vpn_access_real_vessel_requests")
        if self.postgres.exec_query(query_str):
            print("Account VPN Access table successfully created!")


        #ACCOUNT_VPN_ACCESS_REAL_VESSEL
        query_str = """
                CREATE TABLE public.account_vpn_access_real_vessel (
                    id serial NOT NULL,
                    add_job_id int8,
                    remove_job_id int8,
                    account_ip_address varchar(16) NOT NULL,
                    account_id int8 NULL,
                    is_active int2 NULL,
                    date_created timestamp NULL DEFAULT CURRENT_TIMESTAMP,
                    last_update_date timestamp NULL,
                    CONSTRAINT account_vpn_access_real_vessel_job_id_fkey FOREIGN KEY (add_job_id) REFERENCES vpn_access_real_vessel_requests(job_id) ON  DELETE cascade--,
                );
            """
        print("Create table: account_vpn_access_real_vessel")
        if self.postgres.exec_query(query_str):
            print("Account ACCOUNT_VPN_ACCESS_REAL_VESSEL table successfully created!")

        # CLOSE CONNECTION
        self.postgres.close_connection()

    def create_default_entries(self):

        # VPN-ACCESS - CONFIG-FILE  (WEB_API)
        data = {}
        data['config_file_name'] = 'WEB_API_VPN_DEFAULT_CONFIGURATION_FILE'
        print("Create default vpn-access-conf-file: ", data['config_file_name'])
        self.postgres.insert('vpn_access_conf_file', data)

        # VPN-ACCESS - CONFIG-FILE (VESSEL)
        data = {}
        data['config_file_name'] = 'VESSEL_VPN_DEFAULT_CONFIGURATION_FILE'
        print("Create default vpn-access-conf-file: ", data['config_file_name'])
        self.postgres.insert('vpn_access_conf_file', data)

        #1    CLIENT                                  172.16.0.0/24 - 172.23.0.0/24
        # VPN-ACCESS CLIENT
        data = {}
        data['vpn_type'] = 'CLIENT'
        data['prefix'] = 'CLI'
        data['config_file_name'] = 'WEB_API_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '172'
        data['octet_2_min'] = '16'
        data['octet_2_max'] = '23'
        data['octet_3_min'] = '1'
        data['octet_3_max'] = '254'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        #4    UNKNOWN                                 10.8.80.0 - 10.8.84.0
        # VPN-ACCESS GBF
        data = {}
        data['vpn_type'] = 'UNKNOWN'
        data['prefix'] = 'UNKN'
        data['config_file_name'] = 'WEB_API_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '10'
        data['octet_2_min'] = '8'
        data['octet_2_max'] = '8'
        data['octet_3_min'] = '80'
        data['octet_3_max'] = '84'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        #1    VGBF         GLOBAL BRAINFORCE INC.                  10.10.10.0 - 10.10.13.0   (10.10.10.0/24)
        # VPN-ACCESS-VESSEL CLIENT
        data = {}
        data['vpn_type'] = 'VGBF'
        data['prefix'] = 'VGBF'
        data['config_file_name'] = 'VESSEL_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '10'
        data['octet_2_min'] = '10'
        data['octet_2_max'] = '10'
        data['octet_3_min'] = '10'
        data['octet_3_max'] = '13'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        #2    VRH          RADIO HOLLAND                           10.10.20.0 - 10.10.23.0   (10.10.20.0/24)
        # VPN-ACCESS-VESSEL CLIENT
        data = {}
        data['vpn_type'] = 'VRH'
        data['prefix'] = 'VRH'
        data['config_file_name'] = 'VESSEL_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '10'
        data['octet_2_min'] = '10'
        data['octet_2_max'] = '10'
        data['octet_3_min'] = '20'
        data['octet_3_max'] = '23'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        #3    VCLIENT      CLIENT                                  172.24.0.0/24 - 172.31.0.0/24
        # VPN-ACCESS-VESSEL CLIENT
        data = {}
        data['vpn_type'] = 'VCLIENT'
        data['prefix'] = 'VCLI'
        data['config_file_name'] = 'VESSEL_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '172'
        data['octet_2_min'] = '24'
        data['octet_2_max'] = '31'
        data['octet_3_min'] = '1'
        data['octet_3_max'] = '254'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        #4    VESSEL       REAL-VESSEL                             10.20.0.0 - 10.80.0.0   (10.20.0.0/24)
        # VPN-ACCESS-VESSEL CLIENT
        data = {}
        data['vpn_type'] = 'VESSEL'
        data['prefix'] = 'VSL'
        data['config_file_name'] = 'VESSEL_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '10'
        data['octet_2_min'] = '20'
        data['octet_2_max'] = '80'
        data['octet_3_min'] = '1'
        data['octet_3_max'] = '254'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        #5    VUNKNOWN     VESSEL UNKNOWN                          10.10.80.0 - 10.10.84.0
        # VPN-ACCESS-VESSEL CLIENT
        data = {}
        data['vpn_type'] = 'VUNKNOWN'
        data['prefix'] = 'VUNK'
        data['config_file_name'] = 'VESSEL_VPN_DEFAULT_CONFIGURATION_FILE'
        data['octet_1'] = '10'
        data['octet_2_min'] = '10'
        data['octet_2_max'] = '10'
        data['octet_3_min'] = '80'
        data['octet_3_max'] = '84'
        data['octet_4_min'] = '1'
        data['octet_4_max'] = '254'
        data['current_ip_1'] = '0.0.0.0'
        data['current_ip_2'] = '0.0.0.0'
        print("Create default vpn-access: ", data['vpn_type'])
        self.postgres.insert('vpn_access', data)

        # VPN_ACCESS_REQUESTS_STATUS - ON-GOING
        data = {}
        data['status'] = 'ON-GOING'
        data['description'] = 'Creation of VPN is Ongoing.'
        print("Create default VPN_ACCESS_REQUESTS_STATUS: ", data['status'])
        self.postgres.insert('vpn_access_requests_status', data)

        # VPN_ACCESS_REQUESTS_STATUS - DENIED
        data = {}
        data['status'] = 'DENIED'
        data['description'] = 'Problem Occured during creation of VPN'
        print("Create default VPN_ACCESS_REQUESTS_STATUS: ", data['status'])
        self.postgres.insert('vpn_access_requests_status', data)

        # VPN_ACCESS_REQUESTS_STATUS - INITIALIZED
        data = {}
        data['status'] = 'INITIALIZED'
        data['description'] = 'Request has been initialized.'
        print("Create default VPN_ACCESS_REQUESTS_STATUS: ", data['status'])
        self.postgres.insert('vpn_access_requests_status', data)

        # VPN_ACCESS_REQUESTS_STATUS - FINISHED-VS
        data = {}
        data['status'] = 'FINISHED-VS'
        data['description'] = 'Process in Vessel Server are done.'
        print("Create default VPN_ACCESS_REQUESTS_STATUS: ", data['status'])
        self.postgres.insert('vpn_access_requests_status', data)

        # VPN_ACCESS_REQUESTS_STATUS - DONE
        data = {}
        data['status'] = 'DONE'
        data['description'] = 'All of the vpn creation process is complete.'
        print("Create default VPN_ACCESS_REQUESTS_STATUS: ", data['status'])
        self.postgres.insert('vpn_access_requests_status', data)

        # VPN_ACCESS_REQUESTS_STATUS - CONN-ERR
        data = {}
        data['status'] = 'CONN-ERR'
        data['description'] = 'Cannot Connect using ssh.'
        print("Create default VPN_ACCESS_REQUESTS_STATUS: ", data['status'])
        self.postgres.insert('vpn_access_requests_status', data)

        # VPN_ACCESS_REQUESTS - WEB-API VPN
        data = {}
        data['job_id'] = -1
        data['account_id'] = -1
        data['status_details'] = 'For manually added EXISTING WEB-API USER.'
        print("Create default VPN_ACCESS_REQUESTS - For manually added EXISTING WEB-API USER: ", data['job_id'])
        self.postgres.insert('vpn_access_requests', data)

        # VPN_ACCESS_REQUESTS - REAL-VESSEL VPN
        data = {}
        data['job_id'] = -2
        data['account_id'] = -2
        data['status_details'] = 'For manually added EXISTING REAL-VESSEL.'
        print("Create default VPN_ACCESS_REQUESTS - For manually added EXISTING REAL-VESSEL-ACCOUNT: ", data['job_id'])
        self.postgres.insert('vpn_access_requests', data)

        # VPN_ACCESS_REQUESTS - REAL-VESSEL VPN
        data = {}
        data['job_id'] = -3
        data['account_id'] = -3
        data['status_details'] = 'For manually creation of REAL-VESSEL VPN.'
        print("Create default VPN_ACCESS_REQUESTS - For manually creation of REAL-VESSEL-SERVER VPN: ", data['job_id'])
        self.postgres.insert('vpn_access_requests', data)



class Script_Saver_For_Existing_IP:
    python_executable_path = '/usr/bin/python3.5'

    def run(self):
        cmd = '{} script_saver_for_existing_ip.py'.format(self.python_executable_path)
        os.system(cmd)


def main():

    # INIT CONFIG
    config = ConfigParser()
    # CONFIG FILE
    config.read("config/config.cfg")

    server_type = configSectionParser(config,"SERVER")['server_type']

    if server_type != 'production':
        setup = Setup()
        setup.main()

        #THIS IS FOR SAVING THE EXISTING IP
        ask = "Save Existing IP (y/n)?: "
        if input(ask).lower() == 'y':
            script_existing = Script_Saver_For_Existing_IP()
            script_existing.run()

    else:
        print("YOU'RE TRYING TO UPDATE LIVE SERVER!!!")


if __name__ == '__main__':
    main()
