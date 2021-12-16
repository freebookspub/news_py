#coding:utf-8
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import pymysql
import json
import logging
import re
import uuid

HOST= "130.61.52.228"
DATABASE="newsdb"
USER="newsuser"
PASSWORD="sDsd@#E$%&e9d"

HOST= "130.61.52.228"
DATABASE="tempnews"
USER="tempnewsadmin"
PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.foxnews.com"

headers = {
    "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
}
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='foxnews.log',
                    filemode='w')


def get_hash():
    return str(uuid.uuid1()).replace("-", "")


#插入基本信息
def insert_nytimes(href, src, title, desc, v):
    if deduplication_url(href) is None:
        sql = """
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(sql, (href, src, title, desc,'us', 'foxnews', v, get_hash()))
            conn.commit()
        except:
            conn.rollback()


#去重
def deduplication_url(url):
    sql = """
        select * from news where href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()



#插入详情
def insert_details(nytimes_id,content):
    sql = """
        insert into details(news_id,content) values(%s, %s)
    """
    try:
        cursor.execute(sql, (nytimes_id, content))
        conn.commit()
    except:
        conn.rollback()

#获取未爬取详情页的数据
def get_nytimes():
    sql = """
        select * from news where status = 0 and source = 'foxnews'
    """
    cursor.execute(sql)
    return cursor.fetchall()


#修改状态
def update_nytimes(id, status):
    sql = "update news set status = %s where id = %s"
    try:
        cursor.execute(sql, (status, id))
        conn.commit()
    except:
        conn.rollback()


#请求详情页
def request_details(href):
    r = requests.get(href, headers = headers)
    return r.content


#解析首页html
def parse_first_html(content):
    soup = BeautifulSoup(content, "html.parser")
    scripts = soup.find_all("script")
    context = ''
    for script in scripts:
        if 'window.__NUXT__=' in str(script):
            context = str(script).split("window.__NUXT__=")[1].split(";</script>")[0]
    return context


def parse_first_json(content, v):
    print (content)
    # content_json = json.loads(content)
    # content_json = content

    # main = content_json['state']['Layouts']['sectionLayout']['main']
    # print(main)
    # for obj in main:
    #     is_obj = obj['is']
    #     if is_obj == 'advanced-media':
    #         continue
    #     items = obj['props']['items']
    #     for item in items:
    #         title = item['title']
    #         imgs = item['imageUrl']
    #         parsed = urlparse(imgs)
    #         imageUrl = parsed.scheme + '://' + parsed.netloc + parsed.path
    #         if item['category']['name'] == 'VIDEO' or 'video.foxnews.com' in item['url']:
    #             url = item['url']
    #         else :
    #             url = base_url + item['url']
    #         description = item['description'] if 'description' in item else ''
    #         insert_nytimes(url, imageUrl, title, description, v)
    #
    #




#解析详情页
def parse_detail_json(content, url, foxnews_id):
    try:
        if 'video' in url:
            return
        content_json = json.loads(content)
        components = content_json['state']['Articles']['fullArticles'][url[12:]]['components']
        content = []
        for component in components:
            is_obj = component['is']
            if is_obj == 'VideoInline':
                continue
            if is_obj == 'paragraph':
                content.append(component['props']['text'])
            elif is_obj == 'ArticleImage':
                content.append("<img src = '%s'/>" % (component['props']['url']) + component['props']['imageAlt'])
            elif is_obj == 'Slider':
                items = component['props']['items']
                for item in items:
                    content.append("<img src = '%s'/>" % (item['imageUrl']) + item['caption'])
        insert_details(foxnews_id, json.dumps(content))
        update_nytimes(foxnews_id, finshed_succes)
        logging.info("parse_detail_json success, foxnews_id = %s", foxnews_id)
    except:
        update_nytimes(foxnews_id, finshed_error)
        logging.info("parse_detail_json error, foxnews_id = %s", foxnews_id)




def parse_detail_html(content):
    soup = BeautifulSoup(content, "html.parser")
    scripts = soup.find_all("script")
    for script in scripts:
        if 'window.__NUXT__=' in str(script):
            return str(script).split("window.__NUXT__=")[1].split(";</script>")[0]



def parse_detail():
    bbc_list = get_nytimes()
    for bbc in bbc_list:
        print (bbc[1])
        try:
            json_content = parse_detail_html(request_details(bbc[1]))
            parse_detail_json(json_content, bbc[1], bbc[0])
        except:
            logging.error("error, url = %s" %  bbc[0])

def main():
    url = base_url
    tab_dict = {
        '/us' : 'us',
        '/politics' : 'politics',
        '/media': 'media',
        '/opinion' : 'opinion',
        '/entertainment' : 'arts',
        '/sports' : 'sports',
        '/lifestyle' : 'style'
    }
    for k,v in tab_dict.items():
        r = requests.get(url + k, headers = headers)
        parse_first_json(parse_first_html(r.content), v)
        time.sleep(1)
    # parse_detail()




if __name__ == '__main__':
    main()
