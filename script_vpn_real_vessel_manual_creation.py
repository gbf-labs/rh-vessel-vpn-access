from vpn_access import Vpn_Access_Main, Vpn_Access_Create
import argparse
from library.postgresql_queries import PostgreSQL

def vpn_terminal_receiver():
    '''
        usage:
            python script_vpn_real_vessel_manual_creation.py -vessel_number <vessel-number> -vessel_name <vessel_name> -account_os <vessel-os>

        eg. [terminal command]:
            python script_vpn_real_vessel_manual_creation.py -vessel_number 1 -vessel_name LABO1 -vessel_os LINUX

        help:
            python script_vpn_real_vessel_manual_creation.py -h
    '''

    print('\n***[START] SCRIPT_VPN_REAL_VESSEL_MANUAL_CREATION. \n\n')

    parser = argparse.ArgumentParser()
    parser.add_argument('-vessel_number', action='store', dest='vessel_number', help='Vessel Number - must be unique')
    parser.add_argument('-vessel_name', action='store', dest='vessel_name', help="Vessel Name")
    parser.add_argument('-vessel_os', action='store', dest="vessel_os", help='Account OS - LINUX/WINDOWS')

    results = parser.parse_args()

    vessel_number = int(results.vessel_number)
    vessel_name = results.vessel_name
    vessel_os = results.vessel_os

    assert vessel_number
    assert vessel_name
    assert vessel_os


    # GET ID OF DEFAULT TABLE-ID OF MANUAL-INSERTED REAL-VESSEL BASED ON JOB-ID'S -3
    postgresql_query = PostgreSQL()
    manual_realvessel_tbl_id = None
    postgresql_query.connection()
    sql_str = "select * from vpn_access_requests where job_id = -3"
    result = postgresql_query.query_fetch_one(sql_str)
    postgresql_query.close_connection()
    if hasattr(result, 'get'):
        manual_realvessel_tbl_id = result['id']

    ##### FINAL DATA
    id_vpn_access_requests = manual_realvessel_tbl_id    # DEFAULT FOR MANUAL CREATION - [DO NOT CHANGE THIS]
    vpn_type = 'VESSEL'           # DEFAULT - [DO NOT CHANGE THIS]
    account_id = vessel_number
    account_name = vessel_name
    account_os = vessel_os

    vpn_access_create = Vpn_Access_Create(
        id_vpn_access_requests,
        account_id,
        account_name,
        vpn_type,
        account_os
    )
    vpn_access_create.create_static_ip()
    if vpn_access_create.current_ip_1:
        print('\n\n')
        print('-'*50)
        print('ZIP FILE PATH: {}'.format(vpn_access_create.zip_file_path))
        print('-'*50)


    print('\n\n***[DONE] SCRIPT_VPN_REAL_VESSEL_MANUAL_CREATION.\n')


if __name__ == "__main__":

    vpn_terminal_receiver()
