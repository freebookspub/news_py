#coding:utf-8
import time

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
#
# HOST= "130.61.52.228"
# DATABASE="tempnews"
# USER="tempnewsadmin"
# PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.cbsnews.com/"

headers = {
    "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
}
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='cbsnews.log',
                    filemode='w')



def get_hash():
    return str(uuid.uuid1()).replace("-", "")


#插入基本信息
def insert_nytimes(href, src, title, desc, menu):
    if deduplication_url(href) is None:
        sql = """
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (href, src, title, desc,'us', 'cbsnews', menu, get_hash()))
        conn.commit()


#去重
def deduplication_url(url):
    sql = """
        select * from news where source = 'cbsnews' and href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()



#插入详情
def insert_details(nytimes_id,content):
    sql = """
        insert into details(news_id,content) values(%s, %s)
    """
    cursor.execute(sql, (nytimes_id, content))
    conn.commit()

#获取未爬取详情页的数据
def get_nytimes():
    sql = """
        select * from news where status = 0 and source = 'cbsnews'
    """
    cursor.execute(sql)
    return cursor.fetchall()


#修改状态
def update_nytimes(id, status):
    sql = "update news set status = %s where id = %s"
    cursor.execute(sql, (status, id))
    conn.commit()


#请求详情页
def request_details(href):
    r = requests.get(href, headers = headers)
    return r.content


#解析首页html
def parse_first_html(content, menu):
    soup = BeautifulSoup(content, "html.parser")
    articles = soup.find_all("article")
    for article in articles:
        href = article.a.get('href').strip()
        img = article.img.get('src').strip()
        title = article.h4.get_text().strip()
        desc = article.p.get_text().strip()
        insert_nytimes(href, img, title, desc, menu)

def parse_detail_html(id, content):
    try:
        soup = BeautifulSoup(content, "html.parser")
        content_body = soup.find('section', attrs = {'class' : 'content__body'})
        if content_body is None:
            content_body = soup.find('div', attrs = {'class' : 'content__body'})
        p_list =content_body.find_all('p')
        content = []
        for p in p_list:
            content.append(p.get_text())
        insert_details(id, json.dumps(content))
        update_nytimes(id, finshed_succes)
    except:
        update_nytimes(id, finshed_error)
        logging.info("parse_detail_json error, foxnews_id = %s", id)

def parse_detail():
    bbc_list = get_nytimes()
    for bbc in bbc_list:
        parse_detail_html(bbc[0], request_details(bbc[1]))
        time.sleep(1)


def main():
    tab_list = [
        'us',
        'world',
        'politics',
        'entertainment',
        'health',
        'moneywatch',
        'technology',
        'science',
        'crime',
    ]
    for tab in tab_list:
        url = base_url + tab
        r = requests.get(url, headers = headers)
        parse_first_html(r.content, tab)
        time.sleep(1)
    parse_detail()




if __name__ == '__main__':
    main()
