import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from library.config_parser import configSectionParser
from configparser import ConfigParser
import os

class PostgreSQL():

    # INITIALIZE
    def __init__(self):

        # INIT CONFIG
        self.config = ConfigParser()

        config_path = "/home/uvpn/vpn_access/config/config.cfg"
        self.config.read(config_path)

        # SET CONFIG VALUES
        self.host = configSectionParser(self.config,"POSTGRES")['host']
        self.user = configSectionParser(self.config,"POSTGRES")['username']
        self.password = configSectionParser(self.config,"POSTGRES")['password']
        self.dbname = configSectionParser(self.config,"POSTGRES")['db_name']
        self.port = configSectionParser(self.config,"POSTGRES")['port']

    def connection(self, db_name=False):

        # CONNECT TO DATABASE
        try:
            if db_name:
                conn = psycopg2.connect(host=self.host, port=self.port, user=self.user, password=self.password)
            else:
                conn = psycopg2.connect(host=self.host, port=self.port, database=self.dbname, user=self.user, password=self.password)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        except Exception as err:
            print(err)
            raise

        # INSTANTIATE CURSOR
        self.conn = conn
        self.cursor = conn.cursor()

    def close_connection(self):

        self.conn.close()

    def create_database(self,db_name):

        print("Create Database: ", db_name)

        try:
            self.cursor.execute('CREATE DATABASE %s' % db_name)
            self.cursor.close()
            print("Database successfully created!")

        except Exception as err:
            print(err)

    def exec_query(self, query, flag=False):
        try:
            self.cursor.execute(query)

            if flag:
                return self.cursor.fetchone()[0]

            return 1

        except Exception as err:
            print(err)
            return 0

    def insert(self, table, datas, table_id=False):
        try:
            self.connection()

            col = ""
            val = ""
            count = 1
            for data in datas.keys():
                col += data
                if type(datas[data]) in [int, bool, float]:
                    val += str(datas[data])
                else:
                    val += "'" + str(datas[data]) + "'"

                if len(datas) != count:
                    col += ", "
                    val += ", "

                count += 1

            str_query = "INSERT INTO " + table + " (" + col + ")"
            str_query += " VALUES (" + val + ")"

            if table_id:
                str_query += " RETURNING " + table_id

            id_created = self.exec_query(str_query, True)
            if id_created:
                self.conn.commit()
                self.close_connection()
                return id_created

            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            print(err)
            return 0

    def update(self, table, datas, conditions):
        try:

            self.connection()

            str_query = "UPDATE " + table + " SET"

            count = 1
            for data in datas.keys():
                str_query += " " + data + "="

                if type(datas[data]) in [int, bool, float]:
                    str_query += str(datas[data])
                else:
                    str_query += "'" + str(datas[data]) + "'"


                if len(datas) != count:
                    str_query += ", "

                count += 1

            str_query += " WHERE "

            count = 1
            for condition in conditions:
                str_query += str(condition['col']) + " " + str(condition['con']) + " "

                if type(condition['val']) in [int, bool, float, list]:

                    if type(condition['val']) == list:
                        condition['val'] = "(" + ",".join(str(x) for x in condition['val']) + ")"

                    str_query += str(condition['val'])

                else:
                    str_query += "'" + str(condition['val']) + "'"

                if len(conditions) != count:
                    str_query += " AND "

                count += 1

            # EXECUTE QUERY
            if self.exec_query(str_query):
                self.conn.commit()
                self.close_connection()
                return 1
            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            print(err)
            return 0

    def delete(self, table, conditions):

        try:
            self.connection()

            str_query = "DELETE FROM " + table + " WHERE "

            count = 1
            for condition in conditions:
                str_query += str(condition['col']) + " " + str(condition['con']) + " "

                if type(condition['val']) in [int, bool, float, list]:

                    if type(condition['val']) == list:
                        condition['val'] = "(" + ",".join(str(x) for x in condition['val']) + ")"

                    str_query += str(condition['val'])

                else:
                    str_query += "'" + str(condition['val']) + "'"

                if len(conditions) != count:
                    str_query += " AND "

                count += 1

            # EXECUTE QUERY
            if self.exec_query(str_query):
                self.conn.commit()
                self.close_connection()
                return 1

            self.close_connection()
            return 0

        except Exception as err:
            self.close_connection()
            print(err)
            return 0

    # FETCH ONE RETURN JSON DATA
    def query_fetch_one(self, sql_string):

        # QUERY EXECUTE
        self.cursor.execute(sql_string)

        # GET ALL HEADERS
        row_headers=[x[0] for x in self.cursor.description]

        # FETCH ONE DATA
        result = self.cursor.fetchone()

        # CONDITION FOR THE RESULT
        if result:

            # SET RESULT TO JSON
            data = (dict(zip(row_headers,result)))

            # RETURN
            return data

        # RETURN
        return 0

    # FETCH ONE RETURN JSON DATA
    def query_fetch_all(self, sql_string):

        # QUERY EXECUTE
        self.cursor.execute(sql_string)

        # GET ALL HEADERS
        row_headers=[x[0] for x in self.cursor.description]

        # FETCH ALL DATA
        query_result = self.cursor.fetchall()

        # CONDITION FOR THE RESULT
        if query_result:

            # INIT VARIABLE
            data = []

            # LOOP DATA
            for row in query_result:
                # SET RESULT TO JSON
                data.append(dict(zip(row_headers,row)))

            # RETURN
            return data

        # RETURN
        return []
