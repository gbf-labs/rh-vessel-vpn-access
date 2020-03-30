import time
import simplejson
# from library.mysql_database import MySQL_DATABASE
from library.postgresql_queries import PostgreSQL
from flask import jsonify, request, json

class Common():

    # RETURN DATA
    def return_data(self, data):

        # RETURN
        return jsonify(
            data
        )

    # SQL QUERY RETURN CONVERT TO JSON
    def convert_to_json(self, data):

        # INITIALIZE
        json_data=[]

        # LOOP DATA
        for result in data:

            # APPEND JSON DATA
            json_data.append(dict(zip(row_headers,result)))

        # RETURN
        return json.dumps(json_data)

    # REMOVE KEY
    def remove_key(self, data, item):

        # CHECK DATA
        if item in data:

            # REMOVE DATA
            del data[item]

        # RETURN
        return data

    # GET INFO
    def get_info(self, columns, table):

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if not columns: return 0

        # INITIALIZE
        cols  = ''
        count = 1

        # LOOP COLUMNS
        for data in columns:

            # CHECK IF COUNT EQUAL COLUMN LENGHT
            if len(columns) == count:

                # ADD DATA
                cols += data
            else:

                # ADD DATA
                cols += data + ", "

            # INCREASE COUNT
            count += 1

        # CREATE SQL QUERY
        sql_str = "SELECT " + cols + " FROM " + table

        # INITIALIZE DATABASE INFO
        self.my_db = MySQL_DATABASE()

        # CONNECT TO DATABASE
        self.my_db.connection_to_db(self.my_db.database)

        # CALL FUNCTION QUERY ONE
        ret = self.my_db.query_fetch_one(sql_str)

        # CLOSE CONNECTION
        self.my_db.close_connection()

        # RETURN
        return ret

    # GET INFOS
    def get_infos(self, columns, table):

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if not columns: return 0

        # INITIALIZE
        cols  = ''
        count = 1

        # LOOP COLUMNS
        for data in columns:

            # CHECK IF COUNT EQUAL COLUMN LENGHT
            if len(columns) == count:

                # ADD DATA
                cols += data

            else:

                # ADD DATA
                cols += data + ", "

            # INCREASE COUNT
            count += 1

        # CREATE SQL QUERY
        sql_str = "SELECT " + cols + " FROM " + table

        # INITIALIZE DATABASE INFO
        self.my_db = MySQL_DATABASE()

        # CONNECT TO DATABASE
        self.my_db.connection_to_db(self.my_db.database)

        # CALL FUNCTION QUERY ONE
        ret = self.my_db.query_fetch_all(sql_str)

        # CLOSE CONNECTION
        self.my_db.close_connection()

        # RETURN
        return ret

    # GET USER INFO
    def get_user_info(self, columns, table, user_id, token):

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if not columns: return 0

        # INITIALIZE
        cols  = ''
        count = 1

        # LOOP COLUMNS
        for data in columns:

            # CHECK IF COUNT EQUAL COLUMN LENGHT
            if len(columns) == count:

                # ADD DATA
                cols += data

            else:

                # ADD DATA
                cols += data + ", "

            # INCREASE COUNT
            count += 1

        # CREATE SQL QUERY
        sql_str = "SELECT " + cols + " FROM " + table + " WHERE "
        sql_str += " token = '" + token + "'"
        sql_str += " AND id = '" + user_id + "'"

        # INITIALIZE DATABASE INFO
        # self.my_db = MySQL_DATABASE()
        self.postgres = PostgreSQL()

        # CONNECT TO DATABASE
        self.postgres.connection()

        # CALL FUNCTION QUERY ONE
        ret = self.postgres.query_fetch_one(sql_str)

        # CLOSE CONNECTION
        self.postgres.close_connection()

        # RETURN
        return ret

    # VALIDATE TOKEN
    def validate_token(self, token, user_id):

        import datetime
        import dateutil.relativedelta

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if not token: return 0

        # SET COLUMN FOR RETURN
        columns = ['username', 'update_on']

        # CHECK IF TOKEN EXISTS
        user_data = self.get_user_info(columns, "account", user_id, token)

        data = {}
        data['update_on'] = time.time() #datetime.fromtimestamp(time.time())

        condition = []
        temp_con = {}

        temp_con['col'] = 'id'
        temp_con['val'] = user_id
        temp_con['con'] = "="
        condition.append(temp_con)

        self.postgres = PostgreSQL()

        self.postgres.update('account', data, condition)

        # CHECK IF COLUMN EXIST,RETURN 0 IF NOT
        if user_data:

            dt1 = datetime.datetime.fromtimestamp(user_data['update_on'])
            dt2 = datetime.datetime.fromtimestamp(time.time())
            rd = dateutil.relativedelta.relativedelta (dt2, dt1)

            # print(rd.years, rd.months, rd.days, rd.hours, rd.minutes, rd.seconds)
            if rd.years or rd.months or rd.days or rd.hours: return 0
            
            if rd.minutes > 30: return 0

        else: return 0

        # RETURN
        return 1

    def device_complete_name(self, name, number=''):

        # SET READABLE DEVICE NAMES
        humanize_array = {}
        humanize_array['NTWCONF'] = 'Network Configuration'
        humanize_array['NTWPERF'] = 'Network Performance ' + str(number)
        humanize_array['COREVALUES'] = 'Core Values'
        humanize_array['IOP'] = 'Irridium OpenPort ' + str(number)
        humanize_array['VDR'] = 'VDR ' + str(number)
        humanize_array['VSAT'] = 'V-SAT ' + str(number)
        humanize_array['MODEM'] = 'MODEM ' + str(number)
        humanize_array['FBB'] = 'FleetBroadBand ' + str(number)
        humanize_array['VHF'] = 'VHF ' + str(number)
        humanize_array['SATC'] = 'SAT-C ' + str(number)

        # RETURN
        return humanize_array[name]

    # COUNT DATA
    def count_data(self, datas, column, item):

        # INITIALIZE
        count = 0

        # LOOP DATAS
        for data in datas:

            # CHECK OF DATA
            if data[column] == item:

                # INCREASE COUNT
                count += 1

        # RETURN
        return count

    # REMOVE KEY
    def remove_data(self, datas, remove):

        ret_data = []

        # CHECK DATA
        for data in datas:
            if not data['device'] in remove: ret_data.append(data)

        # RETURN
        return ret_data

    def set_return(self, datas):
        ret_data = {}
        ret_data['data'] = []
        for data in datas:
            ret_data['data'].append(data['value'])

        return ret_data

    def check_time_lapse(self, current, timestamp):

        from datetime import datetime
        struct_now = time.localtime(current)

        new_time = time.strftime("%m/%d/%Y %H:%M:%S %Z", struct_now)

        vessel_time = time.localtime(timestamp)

        vessel_time = time.strftime("%m/%d/%Y %H:%M:%S %Z", vessel_time)

        vessel_time = vessel_time.split(' ')
        v_time = vessel_time[1]
        v_date = vessel_time[0]

        new_time = new_time.split(' ')
        n_time = new_time[1]
        n_date = new_time[0]


        start_date = datetime.strptime(v_date, "%m/%d/%Y")
        end_date = datetime.strptime(n_date, "%m/%d/%Y")

        # if not abs((start_date-start_date).days):
        if not abs((start_date-end_date).days):

            FMT = '%H:%M:%S'
            tdelta = datetime.strptime(str(n_time), FMT) - datetime.strptime(str(v_time), FMT)

            tdelta = str(tdelta).split(":")

            try:

                if int(tdelta[0]):
                    return 'red'

                if int(tdelta[1]) < 10:
                    return 'green'

                if int(tdelta[1]) < 20:
                    return 'orange'

            except:

                return 'red'
        return 'red'

    def get_ids(self, key, datas):

        module_ids = []

        for data in datas or []:

            module_ids.append(data['module'])

        return module_ids

    def check_request_json(self, query_json, important_keys):

        query_json = simplejson.loads(simplejson.dumps(query_json))

        for imp_key in important_keys.keys():

            if type(query_json.get(imp_key)):

                if not type(query_json[imp_key]) == type(important_keys[imp_key]):

                    return 0

            else:

                return 0

        return 1

    def milli_to_sec(self, millis):
        # SET TO INT
        millis = int(millis)

        # CONVERT
        seconds=(millis/1000)

        # RETURN
        return int(seconds)