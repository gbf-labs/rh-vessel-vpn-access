import sys, os
sys.path.append(os.path.dirname(os.getcwd()))
from vpn_access import Vpn_Access_Main
from library.postgresql_queries import PostgreSQL


def tester():
    print('\n ** VPN TESTER\n')

    OS = [
        'WINDOWS',
        'LINUX'
    ]
    VPN_TYPES = []

    ######################## USER SELECTION
    postgresql_query = PostgreSQL()
    postgresql_query.connection()
    sql_str = "SELECT t1.vpn_type, t2.id, t2.first_name  FROM account_vpn_access t1 "\
              "RIGHT JOIN account t2 ON t2.id=t1.account_id"
    account_vpns = postgresql_query.query_fetch_all(sql_str)
    postgresql_query.close_connection()
    account_vpns_data = { d['first_name']:{'account_id': d['id']} for d in account_vpns}

    for _k, _v in account_vpns_data.items():
        account_vpns_data[_k]['vpn_list'] = [ d['vpn_type'] for d in account_vpns if d['first_name']==_k and d['vpn_type']]

    account_id_list = []
    for d in account_vpns_data.items():
        account_id_list.append(d)

    account_vpns_data_text = []
    for index, d in enumerate(account_id_list):
        _str = "{}.) {} -> {}".format(index+1, d[0], ', '.join(d[1]['vpn_list']))
        account_vpns_data_text.append(_str)

    account_vpns_data_text = '\n'.join(account_vpns_data_text)
    print('\nUser List:')
    print(account_vpns_data_text)
    _selected_accound_id = int((input('select user:> ') or 0))-1
    selected_accound_id = account_id_list[_selected_accound_id][1]['account_id']
    name = account_id_list[_selected_accound_id][0]
    ######################## USER SELECTION

    ######################## VPN-ACCESS SELECTION
    postgresql_query = PostgreSQL()
    postgresql_query.connection()
    sql_str = "SELECT vpn_type FROM vpn_access"
    data = postgresql_query.query_fetch_all(sql_str)
    postgresql_query.close_connection()
    VPN_TYPES = [ d['vpn_type'] for d in data ]
    vpn_str_option = ''.join([ "{}.) {}\n".format(index+1, val) for index, val\
                              in enumerate(VPN_TYPES)])
    print('\nVPN Types:\n{}'.format(vpn_str_option[:-1]))
    selected_vpn_type = int((input('select vpn-type:> ') or 0))-1
    ######################## VPN-ACCESS SELECTION

    print('\nOperating System: \n1.) {}  \n2.) {} '.format(OS[0], OS[1]))
    selected_os = int(input('select os:> ') or 0)-1

    print()
    print('------------------')
    print('selected_account_id:', selected_accound_id)
    print('name:', name)
    print('selected_vpn_type:', VPN_TYPES[selected_vpn_type])
    print('selected_os:', OS[selected_os])
    print('------------------')
    input('enter to continue:>')

    if selected_accound_id>=0 and name and selected_vpn_type>=0 and selected_os>=0:
        try:
            vpn_access = Vpn_Access_Main(1111, selected_accound_id,
                            name, vpn_type=VPN_TYPES[selected_vpn_type], account_os=OS[selected_os])
            vpn_access.generate()
        except IndexError:
            print("INDEX-ERROR.")
        except:
            print(sys.exc_info())
    else:
        print("\nInvalid selection.")


if __name__ == '__main__':
    print('penn-vpn-access')
    tester()
