#coding:utf-8
import string

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

import pymysql
import json
import logging
import time
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

base_url = "https://www.rnz.co.nz/"
website = "https://www.rnz.co.nz"

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


def insert_list(href, src, title, desc, tab, country, name):
    if deduplication_url(href, name) is None:
        sql = """
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(sql, (href, src, title, desc, country, name, tab, get_hash()))
            conn.commit()
        except:
            conn.rollback()


def deduplication_url(url, name):
    sql = """
        select * from news where source=%s and href = %s
    """
    cursor.execute(sql, (name, url))
    return cursor.fetchone()



def insert_details(news_id, src, content):
    sql = """
        insert into details(news_id, src, content) values(%s, %s, %s)
    """
    try:
        cursor.execute(sql, (news_id, src, content))
        conn.commit()
    except:
        conn.rollback()

def get_url(name):
    sql = """
        select * from news where status = 0 and source = %s
    """
    cursor.execute(sql, (name))
    return cursor.fetchall()


def update_statue(id, status):
    sql = "update news set status = %s where id = %s"
    try:
        cursor.execute(sql, (status, id))
        conn.commit()
    except:
        conn.rollback()

def parse_top(html, tab, country, name):
    soup = BeautifulSoup(html, "html.parser")
    div = soup.find('ul', class_='list-format--wide')
    lists = div.findAll('li', class_='o-digest o-digest--news o-digest--standard u-blocklink has-thumbnail')
    for article in lists:
        try:
            href = website + article.find("a", class_="u-blocklink__overlay-link").get('href')
            title = article.h3.get_text()
            imgs = article.find('img')
            pngurl = imgs.get('src')
            desc = article.find('p').get_text()
            insert_list(href, pngurl, title, desc, tab, country, name)
            # print(tab)
            # print("web:", href)
            # print("title", title)
            # print(imgsurl)
            # print(desc)
            # print("-------------")
        except:
            logging.error("top parse error")



def request_details(href):
    r = requests.get(href, headers = headers)
    return r.content

def parse_content(name):
    lists = get_url(name)
    for list in lists:
        try:
            content = []
            soup = BeautifulSoup(request_details(list[1]), "html.parser")
            body = soup.find("body")
            article = body.find('div', class_='article__body')
            for item in article:
                try:
                    if "p" == item.name:
                        content.append(item.get_text())
                    elif "h2" == item.name:
                        h2 = "<div class=\"head3\">"+ item.get_text() +"</div>"
                        content.append(h2)
                    elif "div" == item.name:
                        figure = item.find("img")
                        imgs, alt = getImg(figure)
                        htmlimg = "<img src=\""+imgs+ "\" alt=\""+ alt + "\" class=\"abcImg\"></img>"
                        content.append(htmlimg)
                        imgtext = item.find('p').get_text()
                        if imgtext:
                           text = "<div class=\"imgText\">" + imgtext + "</div>"
                           content.append(text)
                except:
                    logging.error("aaaabbb")
            insert_details(list[0], imgs, json.dumps(content))
            update_statue(list[0], finshed_succes)
        except:
            logging.error("content parse error, id = %s" % list[0])
            update_statue(list[0], finshed_error)
        time.sleep(1)


def getImg(url):
    alt = url.get("alt")
    src = website + url.get("src")
    return src, alt;


def main():
    country = 'nz'
    name = 'rnz'

    tab_list = {
        'national': 'news/national',
        'world': 'news/world',
        'political': 'news/political',
        'sport': 'news/sport',
        'business': 'news/business',
        'country': 'news/country',
        'in-depth': 'news/in-depth',
    }

    for tab, value in tab_list.items():
        url = base_url + value
        r = requests.get(url, headers=headers)
        parse_top(r.content, tab, country, name)
        time.sleep(1)
    parse_content(name)
    conn.close()

if __name__ == '__main__':
    main()

