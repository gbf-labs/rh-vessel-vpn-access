import re
from library.postgresql_queries import PostgreSQL
from datetime import datetime
import time

# with open('./EXISTING_USER_IP_VPN.txt') as f:
# with open('./EXISTING_VESSEL_IP_VPN.txt') as f:

FILE_LIST = ['./FORMATTED_EXISTING_USER_IP_VPN.txt',
             './FORMATTED_EXISTING_VESSEL_IP_VPN.txt',
             'FORMATTED_EXISTING_REAL_VESSEL.txt']

for FILE in FILE_LIST:
    print("\nFile: {}\n".format(FILE))
    with open(FILE) as f:
        text = f.read()
        data_text = text

        result_data = re.findall(r'^(\d+\s+[\w\(\)]+\s+[\d\.]+)$', data_text, re.MULTILINE)

        ip_data_list = []

        for index, d in enumerate(result_data, 1):
            num = re.search(r'(\d+)\s+[\w\(\)+\s+[\d\.]+', d).group(1)
            name = re.search(r'\d+\s+([\w\(\)]+)\s+[\d\.]+', d).group(1)
            ip = re.search(r'\d+\s+[\w\(\)]+\s+([\d\.]+)', d).group(1)

            print(num, name, ip)

            ip_data_list.append({
                'num': index,
                'name': name,
                'ip': ip,
            })

        table_vpn_access_type = {
            'GBF': {
                'ACCEPTED_PREFIX': ['GBF']
            }
            ,'RH': {
                'ACCEPTED_PREFIX': ['RH']
            }
            ,'UNKNOWN':{
                'ACCEPTED_PREFIX': ['UNKNOWN']
            }
            ,'CLIENT':{
                'ACCEPTED_PREFIX': ['Client']
            }
            ,'VESSEL':{
                'ACCEPTED_PREFIX': ['Vessel']
            }
            ,'VCLIENT':{
                'ACCEPTED_PREFIX': ['VClient']
            }
            ,'VGBF':{
                'ACCEPTED_PREFIX': ['VGBF']
            }
            ,'VRH':{
                'ACCEPTED_PREFIX': ['VRH']
            }
        }

        new_data_list = []
        for data in ip_data_list:
            d = data
            for at in table_vpn_access_type.items():
                vpn_type = at[0]
                accepted_prefix_list = at[1]['ACCEPTED_PREFIX']
                for prefix in accepted_prefix_list:
                    if d['name'].startswith(prefix):
                        d['vpn_type'] = vpn_type
                        new_data_list.append(d)

                        break

        print('new_data_list:', new_data_list)
        for d in new_data_list:
            print(d['num'], d['name'], d['ip'], d['vpn_type'])

        if True:

            try:
                postgresql_query = PostgreSQL()
                postgresql_query.connection()

                for d in new_data_list:
                    name = d['name']
                    ip = d['ip']
                    ip_addr_1 = ip
                    last_num = int(re.search(r'\.(\d+)$',ip_addr_1).group(1))
                    ip_addr_2 = re.sub(r'(\d+)$', str(last_num+1), ip_addr_1)

                    data = {}
                    data['manually_added'] = 1
                    data['account_id'] = -1
                    data['id_vpn_access_requests'] = 1
                    data['vpn_type'] = d['vpn_type']
                    data['ip_addr_1'] = ip_addr_1
                    data['ip_addr_2'] = ip_addr_2
                    data['is_active'] = 1
                    created_id = postgresql_query.insert('account_vpn_access', data, table_id='id_vpn_access_requests')
                    table_id = created_id
                    # print('table_id:', table_id)

                    conditions = []
                    conditions.append({
                        "col": "vpn_type",
                        "con": "=",
                        "val": d['vpn_type']
                    })
                    data = {}
                    data['current_ip_1'] = ip_addr_1
                    data['current_ip_2'] = ip_addr_2
                    data['update_on'] = datetime.fromtimestamp(time.time())
                    postgresql_query.update('vpn_access', data, conditions)

            finally:
                postgresql_query.close_connection()

