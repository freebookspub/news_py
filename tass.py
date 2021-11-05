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

HOST= "130.61.52.228"
DATABASE="tempnews"
USER="tempnewsadmin"
PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.tass.com/"
website = "https://www.tass.com"

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
        cursor.execute(sql, (href, src, title, desc, country, name, tab, get_hash()))
        conn.commit()


def deduplication_url(url, name):
    sql = """
        select * from news where source=%s and href = %s
    """
    cursor.execute(sql, (name, url))
    return cursor.fetchone()



def insert_details(news_id, src, alt, content):
    sql = """
        insert into details(news_id, src, alt, content) values(%s, %s, %s, %s)
    """
    cursor.execute(sql, (news_id, src, alt, content))
    conn.commit()

def get_url(name):
    sql = """
        select * from news where status = 0 and source = %s
    """
    cursor.execute(sql, (name))
    return cursor.fetchall()


def update_statue(id, status):
    sql = "update news set status = %s where id = %s"
    cursor.execute(sql, (status, id))
    conn.commit()

def parse_top(html, tab, country, name):
    soup = BeautifulSoup(html, "html.parser")
    print(soup)
    news = soup.find('div', class_="news-list")
    lists = soup.findAll('div', class_='news-list__item ng-scope')
    print(lists)
    for article in lists:
        print(article)
        try:
            href = website + article.find("a").get('href')
            title = article.h3.get_text()
            imgs = article.find('img')
            pngurl = website + imgs.get('src')
            desc = article.find('p').get_text()
            # insert_list(href, pngurl, title, desc, tab, country, name)
            print(tab)
            print("web:", href)
            print("title", title)
            print(pngurl)
            print(desc)
            print("-------------")
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
            headalt = ''
            headimgs = ''
            soup = BeautifulSoup(request_details(list[1]), "html.parser")
            body = soup.find("body")
            article = body.find('div', class_='l-col l-col--8')
            head = article.find('figure', class_="article-featured-image")
            if head:
                headfigure = head.find("img")
                if headfigure:
                    headimgs, headalt = getImg(headfigure)
                    halt = head.find('figcaption')
                    if headimgs is None:
                        headimgs = ''
                    if halt is None:
                        halt = ''
                    else :
                        headalt = halt.get_text()
            alltext = article.find('div', class_='wysiwyg wysiwyg--all-content css-1vsenwb')
            for item in alltext:
                try:
                    if "p" == item.name:
                        ptext = item.get_text().strip()
                        content.append(ptext)
                    elif "h2" == item.name:
                        h2 = "<div class=\"head3\">"+ item.get_text() +"</div>"
                        content.append(h2)
                    elif "figure" == item.name:
                        figure = item.find("img")
                        imgs, alt = getImg(figure)
                        alt = item.get_text()
                        htmlimg = "<img src=\""+imgs+ "\" alt=\""+ alt + "\" class=\"abcImg\"></img>"
                        content.append(htmlimg)
                        imgtext = item.find('figcaption')
                        if imgtext is None:
                            text = "<div class=\"imgText\">" + alt + "</div>"
                        else :
                            alttext = imgtext.get_text()
                            text = "<div class=\"imgText\">" + alttext + "</div>"
                        content.append(text)

                except:
                    logging.error("aaaabbb")
            insert_details(list[0], headimgs, headalt, json.dumps(content))
            update_statue(list[0], finshed_succes)
        except:
            logging.error("content parse error, id = %s" % list[0])
            update_statue(list[0], finshed_error)


def getImg(url):
    alt = url.get("alt")
    src = website + url.get("src")
    return src, alt;


def main():
    country = 'ru'
    name = 'tass'

    tab_list = {
        'world': 'world',
    }

    for tab, value in tab_list.items():
        url = base_url + value
        r = requests.get(url, headers=headers)
        parse_top(r.content, tab, country, name)
        time.sleep(1)
    parse_content(name)


if __name__ == '__main__':
    main()

