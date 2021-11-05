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

# HOST= "130.61.52.228"
# DATABASE="tempnews"
# USER="tempnewsadmin"
# PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.newsweek.com/"
website = "https://www.newsweek.com/"

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
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (href, src, title, desc,'us', 'newsweek', tab, get_hash()))
        conn.commit()


def deduplication_url(url):
    sql = """
        select * from news where source='newsweek' and href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()



def insert_details(news_id, figure, p_list, alt, src, content):
    sql = """
        insert into details(news_id, figure, p_list, alt, src, content) values(%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (news_id, figure, p_list, alt, src, content))
    conn.commit()

def get_nytimes():
    sql = """
        select * from news where status = 0 and source = 'newsweek'
    """
    cursor.execute(sql)
    return cursor.fetchall()


def update_nytimes(id, status):
    sql = "update news set status = %s where id = %s"
    cursor.execute(sql, (status, id))
    conn.commit()

def mainimg(imgurl):
    url = imgurl.find("source", {"type":"image/webp"}).get('data-srcset')
    if url is None:
        url = imgurl.find("source").get("srcset")
        if url is None:
            url = imgurl.find("source").get("data_srcset")

    img = splitFun(url)
    return img

def splitFun(url):
    blank = url
    if ',' in url:
        str = url.split(',')
        blank = str[0]
    if ' ' in blank:
        strblank = blank.split(' ')
        imgs = strblank[0]
        parsed = urlparse(imgs)
        src =parsed.scheme +'://' + parsed.netloc + parsed.path
    return src




def parse_top(html, tab):
    soup = BeautifulSoup(html, "html.parser")
    article_list = soup.find_all("article")
    for article in article_list:
        try:
            h3 = article.find('h3')
            href_half = h3.find("a").get('href')
            href = base_url+href_half
            title = h3.find("a").get_text()
            imgs = mainimg(article)
            desc = article.find('div', class_="summary").get_text()

            insert_nytimes(href, imgs, title, desc, tab)

            # parsed = urlparse(imgs)
            # src =parsed.scheme +'://' + parsed.netloc + parsed.path
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
            alt = ''
            figure = ''
            content = []
            soup = BeautifulSoup(request_details(nytimes[1]), "html.parser")
            article = soup.find("div", class_="article-body v_text paywall")
            for item in article:
                try:
                    if "p" == item.name:
                        text =  item.get_text()
                        if 'Newsweek' in text:
                            print('1')
                        else:
                            content.append(text)
                    elif "h2" == item.name:
                        h2 = "<div class=\"head3\">"+ item.get_text() +"</div>"
                        content.append(h2)
                    elif "figure" == item.name:
                        figure = item.find("picture")
                        if figure:
                            imgs, alt = getImg(figure)
                            htmlimg = "<img src=\"" + imgs + "\" alt=\"" + alt + "\" class=\"abcImg\"></img>"
                            content.append(htmlimg)
                            imgtext = item.find('span', class_="cap").get_text()
                            alt = imgtext
                            text = "<div class=\"imgText\">" + imgtext + "</div>"
                            content.append(text)
                except:
                    logging.error("aaaabbb")
            # print(nytimes[0], figure, article, alt, nytimes[2],  json.dumps(content))
            insert_details(nytimes[0], figure, article, alt, nytimes[2],  json.dumps(content))
            update_nytimes(nytimes[0], finshed_succes)
        except:
            update_nytimes(nytimes[0], finshed_error)
            logging.error("newsweek error, id = %s" % nytimes[0])



def getImg(url):
    setsrc = url.find("source", {"type":"image/webp"}).get("srcset")
    src = splitFun(setsrc)
    return src, '';


def main():
    tab_list = {
        'us': 'us',
        'world': 'world',
        'business': 'business',
        'technology': 'tech-science',
        'sports': 'sports',
        'health': 'health',
        'experts': 'experts',
        'education':'education',
    }
    for tab, value in tab_list.items():
        url = base_url + value
        r = requests.get(url, headers=headers)
        parse_top(r.content, tab)
        time.sleep(1)
    parse_content()


if __name__ == '__main__':
    main()

