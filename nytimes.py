#coding:utf-8

import requests
from bs4 import BeautifulSoup

import pymysql
import json
import logging
import time
import uuid

HOST= "130.61.52.228"
DATABASE="tempnews"
USER="tempnewsadmin"
PASSWORD="FD32sd$7De9ds^&"

HOST= "sql427.main-hosting.eu"
DATABASE="u637214094_spider"
USER="u637214094_spider"
PASSWORD="Aasdfgh12@"

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
            insert into nytimes(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(sql, (href, src, title, desc,'us', 'nytime', tab, get_hash()))
            conn.commit()
        except:
            conn.rollback()


def deduplication_url(url):
    sql = """
        select * from nytimes where href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()



def insert_details(nytimes_id, figure, p_list, alt, src, content):
    sql = """
        insert into nytimes_details(nytimes_id, figure, p_list, alt, src, content) values(%s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(sql, (nytimes_id, figure, p_list, alt, src, content))
        conn.commit()
    except:
        conn.rollback()

def get_nytimes():
    sql = """
        select * from nytimes where status = 0 and source = 'nytime'
    """
    cursor.execute(sql)
    return cursor.fetchall()


def update_nytimes(id):
    sql = "update nytimes set status = 1 where id = %s"
    try:
        cursor.execute(sql, (id))
        conn.commit()
    except:
        conn.rollback()




def parse_top(html, tab):
    soup = BeautifulSoup(html, "html.parser")
    article_list = soup.find_all("article")
    for article in article_list:
        try:
            head_a = article.find("a", attrs={"aria-hidden": "true"})
            href = head_a.get('href')
            src = head_a.find("img").get('src')
            title = article.h2.a.get_text()
            desc = article.p.get_text()
            insert_nytimes(href, src, title, desc, tab)
            print ('爬取的title = %s' % title)
            logging.info("top parse success")
        except:
            logging.error("top parse error")



def request_details(href):
    r = requests.get(href, headers = headers)
    return r.content


def parse_list(html, tab):
    soup = BeautifulSoup(html, "html.parser")
    div_list = soup.find_all("div", attrs={"class": "css-1l4spti"})
    for div in div_list:
        try:
            href = div.a.get('href')
            src = div.img.get('src')
            title = div.h2.get_text()
            desc = div.p.get_text()
            insert_nytimes(href, src, title, desc, tab)
            print ('爬取的title = %s' % title)
            logging.info("list parse success")
        except:
            logging.error("list parse error")


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
            logging.info("content parse success, id = %s" % (nytimes[0]))
        except:
            logging.error("content parse error, id = %s" % nytimes[0])
        update_nytimes(nytimes[0])

def select_all_nytimes():
    sql = """
        select * from nytimes
    """
    cursor.execute(sql)
    return cursor.fetchall()


def update_href():
    sql = """
        update nytimes set href = %s where id = %s
    """
    for nytime in select_all_nytimes():
        cursor.execute(sql, (base_url + nytime[1], nytime[0]))
        conn.commit()

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
        parse_top(r.content, tab)
        parse_list(r.content, tab)
        time.sleep(3)
    parse_content()
    conn.close()


if __name__ == '__main__':
    main()

