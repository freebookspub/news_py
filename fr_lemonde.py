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
DATABASE="tempnews"
USER="tempnewsadmin"
PASSWORD="FD32sd$7De9ds^&"

HOST= "sql427.main-hosting.eu"
DATABASE="u637214094_spider"
USER="u637214094_spider"
PASSWORD="Aasdfgh12@"

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.lemonde.fr/"
website = "https://www.lemonde.fr/"

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
    if deduplication_url(href) is None:
        sql = """
            insert into nytimes(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(sql, (href, src, title, desc,'fr', 'lemonde', tab, get_hash()))
            conn.commit()
        except:
            conn.rollback()


def deduplication_url(url):
    sql = """
        select * from nytimes where source='lemonde' and href = %s
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
        select * from nytimes where status = 0 and source = 'lemonde'
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

def mainimg(imgurl):
    url = imgurl.find("source")
    if url is None:
        img = imgurl.find("img").get("data-src")
    else:
        img = url.get('data-srcset')
    return img



def parse_top(html, tab):
    soup = BeautifulSoup(html, "html.parser")
    lists = soup.find(id='river')
    article_list = lists.find_all("section", class_="teaser teaser--inline-picture")
    for article in article_list:
        try:
            href = article.find("a", class_="teaser__link").get('href')
            imgs = mainimg(article)
            # parsed = urlparse(imgs)
            # # src =parsed.scheme +'://' + parsed.netloc + parsed.path
            title = article.h3.get_text()
            desc = article.find('p', class_="teaser__desc").get_text()
            insert_nytimes(href, imgs, title, desc, tab)
            # print(tab)
            # print(href)
            # print(title)
            # print(imgs)
            # print(desc)
            # print("-------------")
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
            body = soup.find("body")
            header = body.find("header", class_="article__header")
            article = body.find('article')
            hp = header.find("div", class_="article__heading")
            desc = hp.find("p", class_="article__desc")
            try:
                if desc:
                    desctext = desc.get_text()
                    htmldesc = "<div class=\"titledesc\">"+desctext+"</div>"
                    content.append(htmldesc)
            except:
                print("err1111")

            for item in article:
                try:
                    if "p" == item.name:
                        content.append(item.get_text())
                    elif "h2" == item.name:
                        h2 = "<div class=\"head3\">"+ item.get_text() +"</div>"
                        content.append(h2)
                    elif "figure" == item.name:
                        figure = item.find("img")
                        imgs, alt = getImg(figure)
                        htmlimg = "<img src=\""+imgs+ "\" alt=\""+ alt + "\" class=\"abcImg\"></img>"
                        content.append(htmlimg)
                        imgtext = item.find('figcaption').get_text()
                        if imgtext:
                           text = "<div class=\"imgText\">" + imgtext + "</div>"
                           content.append(text)
                except:
                    logging.error("aaaabbb")
            insert_details(nytimes[0], figure, article, alt, imgs,  json.dumps(content))
        except:
            logging.error("content parse error, id = %s" % nytimes[0])
        update_nytimes(nytimes[0])


def getImg(url):
    alt = url.get("alt")
    setsrc = url.get("srcset")
    if setsrc is None:
        setsrc = url.get("data-srcset")
    imgs = setsrc.split(' ')
    src = ''
    for item in imgs:
        try:
            if "https://" in item:
                src = item
        except:
            print('err')
    return src, alt;


def main():
    tab_list = {
        'fr': 'economie-francaise',
        'arts': 'culture',
        'books': 'livres',
        'science': 'sciences',
        'sports': 'sport',
        'food': 'm-gastronomie',
        'travel': 'm-voyage',
        'fashion':'m-mode',
        'style': 'm-styles',
        'news': 'actualite-en-continu'
    }

    for tab, value in tab_list.items():
        url = base_url + value
        r = requests.get(url, headers=headers)
        parse_top(r.content, tab)
        time.sleep(1)
    parse_content()
    conn.close()

if __name__ == '__main__':
    main()

