import sys
import json
import requests
import argparse

from vpn_access import Vpn_Access_Main, Vpn_Access_Create
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
    parser.add_argument('-token', action='store', dest='token', help='Token')
    parser.add_argument('-callback_url', action='store', dest='callback_url', help='Callback - must be URL')
    parser.add_argument('-job_id', action='store', dest='job_id', help='Job ID - must be unique')
    parser.add_argument('-vessel_number', action='store', dest='vessel_number', help='Vessel Number - must be unique')
    parser.add_argument('-vessel_name', action='store', dest='vessel_name', help="Vessel Name")
    parser.add_argument('-vessel_os', action='store', dest="vessel_os", help='Account OS - LINUX/WINDOWS')

    results = parser.parse_args()

    token = results.token
    callback_url = results.callback_url
    job_id = results.job_id
    vessel_number = int(results.vessel_number)
    vessel_name = results.vessel_name
    vessel_os = results.vessel_os

    assert token
    assert callback_url
    assert job_id
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
        print('Data: {}'.format(vpn_access_create))
        print('ZIP FILE PATH: {}'.format(vpn_access_create.zip_file_path))
        print('-'*50)

        vessel_ip_address = vpn_access_create.current_ip_1
        directory = vpn_access_create.zip_file_path
        callback('active', 'ok', directory, callback_url, token, job_id, vessel_ip_address)

        print('\n\n***[DONE] SCRIPT_VPN_REAL_VESSEL_MANUAL_CREATION.\n')
    
    else:

        print("Invalid Data!!!")
        print('-'*50)
        print(token)
        print(callback_url)
        print(job_id)
        print(vessel_number)
        print(vessel_name)
        print(vessel_os)
        print('-'*50)

def callback(status, message, directory, callback_url, token, job_id, vessel_ip_address):
    print("[START] - callback.")

    ## CALLBACK
    try:
        headers = {}
        headers['content-type'] = 'application/json'
        headers['token'] = str(token)
        headers['jobid'] = str(job_id)
        data = {
            'status': status,
            'message': message,
            'directory': directory,
            'action': 'CREATE',
            'vpn_type': 'VESSEL',
            'ip': vessel_ip_address
        }
        print("*"*100)
        print("callback_url: ", callback_url)
        print("headers: ", headers)
        print("data: ", data)
        print("*"*100)
        requests.put(callback_url, data=json.dumps(data), headers=headers)
        sys.exit(0)
    except:
        print('[CALL-BACK-ERROR] >')
        print(sys.exc_info())
        sys.exit(0)

    print("[END] - callback.")

if __name__ == "__main__":

    vpn_terminal_receiver()
