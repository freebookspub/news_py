#coding:utf-8
import json
import logging
import time
import uuid

import pymysql
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

HOST= "130.61.52.228"
DATABASE="newsdb"
USER="newsuser"
PASSWORD="sDsd@#E$%&e9d"

# HOST= "130.61.52.228"
# DATABASE="tempnews"
# USER="tempnewsadmin"
# PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9


conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.nytimes.com"

headers = {
    "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
}
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='nytimes.log',
                    filemode='w')



def get_hash():
    return str(uuid.uuid1()).replace("-", "")


def insert_nytimes(href, src, title, desc, tab):
    href = base_url + href
    if deduplication_url(href) is None:
        sql = """
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (href, src, title, desc,'us', 'nytime', tab, get_hash()))
        conn.commit()


def deduplication_url(url):
    sql = """
        select * from news  where source='nytime' and href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()



def insert_details(nytimes_id, figure, p_list, alt, src, content):
    sql = """
        insert into details(news_id, figure, p_list, alt, src, content) values(%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (nytimes_id, figure, p_list, alt, src, content))
    conn.commit()

def get_nytimes():
    sql = """
        select * from news where status = 0 and source = 'nytime'
    """
    cursor.execute(sql)
    return cursor.fetchall()


def update_nytimes(id, status):
    sql = "update news set status = %s where id = %s"
    cursor.execute(sql, (status, id))
    conn.commit()

def splitFun(urlweb):
    num = ''
    tmp = ''
    url6 = ''
    url7 = ''
    if ',' in urlweb:
        str = urlweb.split(',')
        for item in str:
            if ' ' in item:
                strblank = item.split(' ')
                tmp = strblank[0]
                num = strblank[1]
                if '768' in num:
                    url7 = tmp
                    max
                elif '600' in num:
                    url6 = tmp
                elif url6 == '':
                    url6 = tmp
        if url7:
            imgs = url7
        else:
            imgs = url6
        parsed = urlparse(imgs)
        src =parsed.scheme +'://' + parsed.netloc + parsed.path
    return src



def parse_lists(html, tab):
    soup = BeautifulSoup(html, "html.parser")
    list = soup.find(id="stream-panel")
    article_list = list.find_all('li')
    for article in article_list:
        try:
            head_a = article.find("a")
            href = head_a.get('href')
            title = head_a.h2.get_text()
            desc = head_a.p.get_text()
            src = head_a.find("img").get("srcset")
            img = splitFun(src)
            insert_nytimes(href, img, title, desc, tab)
            logging.info("top parse success")
        except:
            logging.error("top parse error")



def request_details(href):
    r = requests.get(href, headers = headers)
    return r.content

def parse_content():
    nytimes_list = get_nytimes()
    for nytimes in nytimes_list:
        try:
            content = []
            soup = BeautifulSoup(request_details(nytimes[1]), "html.parser")
            figure = soup.figure
            p_list = soup.find_all("p", attrs={"class":"css-axufdj evys1bk0"})
            alt = figure.img.get("alt")
            src = figure.img.get("src")
            for p in p_list:
                content.append(p.get_text())
            insert_details(nytimes[0], figure, p_list, alt, src,  json.dumps(content))
            update_nytimes(nytimes[0], finshed_succes)
        except:
            logging.error("content parse error, id = %s" % nytimes[0])
            update_nytimes(nytimes[0], finshed_error)
        time.sleep(1)


def select_all_nytimes():
    sql = """
        select * from nytimes
    """
    cursor.execute(sql)
    return cursor.fetchall()

def main():
    tab_list = [
        'world',
        'us',
        'politics',
        'nyregion',
        'business',
        'opinion',
        'technology',
        'health',
        'science',
        'sports',
        'arts',
        'books',
        'style',
        'food',
        'travel',
        'magazine',
        't-magazine',
        'realestate',
        'obituaries',
        'upshot'
    ]
    for tab in tab_list:
        r = requests.get("https://www.nytimes.com/section/%s" % tab, headers = headers)
        parse_lists(r.content, tab)
        time.sleep(1)
    parse_content()
    conn.close()

if __name__ == '__main__':
    main()

