# -*- coding: utf-8 -*-

import pymysql
import requests
import oss2
import uuid

#阿里oss
auth = oss2.Auth('LTAI4GDvTdUDD5fkY9kUTUFX', 'Sfo3RdBSJB4ZRFafYhdzbDQBEKqFYo')
bucket = oss2.Bucket(auth, 'http://oss-cn-zhangjiakou.aliyuncs.com', 'fun-gen-cn-zhangjiakou-1363763281471079')


#mysql
HOST= "sql427.main-hosting.eu"
DATABASE="u637214094_spider"
USER="u637214094_spider"
PASSWORD="Aasdfgh12@"
conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()


def put_object_from_file():
    bucket.put_object_from_file('news/ASIA.png', 'C:\\Users\\mico\\Desktop\\ASIA.png')

def put_object(filename, content):
    result = bucket.put_object("news/{0}".format(filename), content)
    print ("filename: {0}".format(filename))
    print('http status: {0}'.format(result.status))


def find_first_img():
    sql = """
        select id, img_url from nytimes where load_img = '' or load_img is null  and source ='bbc' or source ='nytimes' or source ='newsweek'
    """
    cursor.execute(sql)
    return cursor.fetchall()

def find_detail_img():
    sql = """
        select id, src from nytimes_details where (src != '' or src is not null) and (local_src = '' or local_src is null)
    """

    cursor.execute(sql)
    return cursor.fetchall()


def update_first_img(id, img):
    sql = """
        update nytimes set load_img = %s where id = %s
    """
    try:
        cursor.execute(sql, (img, id))
        conn.commit()
    except:
        conn.cursor()


def update_detail_img(id, img):
    sql = """
        update nytimes_details set local_src = %s where id = %s
    """
    try:
        cursor.execute(sql, (img, id))
        conn.commit()
    except:
        conn.cursor()

def request_url(url):
    r = requests.get(url)
    return r.content

def download_list():
    img_list = find_first_img()
    for img in img_list:
        suffix = img[1].split('/')[-1].split('?')[0][-4:]
        filename = str(uuid.uuid1()) + suffix
        print (img[0])
        #print (filename)
        try:
            put_object(filename, request_url(img[1]))
            update_first_img(img[0], filename)
        except:
            print ("error")


def download_detail():
    img_list = find_detail_img()
    for img in img_list:
        if img[1] != '':
            suffix = img[1].split('/')[-1].split('?')[0][-4:]
            filename = str(uuid.uuid1()) + suffix
            print (img[0])
            #print (filename)
            try:
                put_object(filename, request_url(img[1]))
                update_detail_img(img[0], filename)
            except:
                print ("error")






if __name__ == '__main__':
    download_list()
    download_detail()
