#coding:utf-8

import json
import logging
import re
#from clickhouse_driver import Client
import torndb


HOST= "127.0.0.1"
DATABASE="nytimes"
USER="root"
PASSWORD="123456"

# HOST= "sql427.main-hosting.eu"
# DATABASE="u637214094_spider"
# USER="u637214094_spider"
# PASSWORD="Aasdfgh12@"

# logging.basicConfig(level=logging.INFO,
#                     format='%(levelname)s %(message)s',
#                     datefmt='%a, %d %b %Y %H:%M:%S',
#                     filename='email.log',
#                     filemode='w')


#client = Client(host='10.1.2.152',port='9000',user="dba" ,password="nc3Bx01q", database= "warehouse")
torndbclient = torndb.Connection(host=HOST, database=DATABASE, user= USER, password=PASSWORD)

def insert_email(string):
    sql = """
        insert into email(email) values (%s)
    """
    torndbclient.insert(sql, string)

def insert():
    f=open('email.log', 'rb')
    for string in f.readlines():
        string = string.split(' ')[1]
        if string is not None and '.com' in string:
            print (string)
            insert_email(string)



def email():
    sql = """
        select email from s_users where email is not null limit 0, 1000000
    """
    for string in client.execute(sql):
        logging.info("%s" % (string))

if __name__ == '__main__':
    insert()

