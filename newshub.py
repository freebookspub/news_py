#coding:utf-8
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

import pymysql
import json
import logging
import re

from lxml import etree
import dateparser
from bs4 import BeautifulSoup
import uuid

index_url = "https://www.newshub.co.nz"
url = "https://www.newshub.co.nz/home/new-zealand.html"

countrycode = 'nz'
website = 'newshub'

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
headers = {
    "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
}

conn = pymysql.connect( host=HOST, database=DATABASE, user=USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()


#插入基本信息
def insert_item(href, src, title, desc, k):
    if deduplication_url(href) is None:
        sql = """
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (href, src, title, desc, 'nz', 'newshub', k, get_hash()))
        conn.commit()

#去重
def deduplication_url(url):
    sql = """
        select * from news where href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()

def update_nytimes(id, status):
    sql = "update news set status = %s where id = %s"
    cursor.execute(sql, (status, id))
    conn.commit()


def get_lists():
    sql = """
            select * from news where status = 0 and source = 'newshub'
        """
    cursor.execute(sql)
    return cursor.fetchall()
def insert_details(nytimes_id, figure, p_list, alt, src, content):
    sql = """
        insert into details(news_id, figure, p_list, alt, src, content) values(%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (nytimes_id, figure, p_list, alt, src, content))
    conn.commit()

def get_detail_html(url, list):
    response = requests.get(url)
    # html = etree.HTML(response.text)
    # frame_url = index_url + html.xpath('//div/@data-belt-path')[-1]
    # response = requests.get(frame_url)
    soup = BeautifulSoup(response.text, "html.parser")
    body = soup.find("body")
    text = body.findAll("div", class_='text parbase section')
    content = []
    try:
        for line in text:
            alp = line.findAll("p")
            for item in alp:
                if "p" == item.name:
                    content.append(item.get_text())
        insert_details(list[0], '', '', '', list[2], json.dumps(content))
        update_nytimes(list[0], finshed_succes)
    except:
        update_nytimes(list[0], finshed_error)

def get_detail():
    lists = get_lists()
    for list in lists:
        get_detail_html(list[1], list)

def get_hash():
    return str(uuid.uuid1()).replace("-", "")


def lists(html, tab):
    soup = BeautifulSoup(html, "html.parser")
    section = soup.find('section', class_="Story")
    lists = section.find_all('div', class_="Story-item")
    assert lists, Exception("not find item_list")
    for article in lists:
        try:
            head_a = article.find("a", class_="c-NewsTile-imageLink")
            href = head_a.get('href')
            src = head_a.find("img").get('srcset')
            title = article.h2.get_text()
            desc = article.p.get_text()
            insert_item(href, src, title, desc, tab)
            logging.info("top parse success")
        except:
            logging.error("top parse error")


def get_html(url, tab):
    response = requests.get(url, headers=headers)
    # html = etree.HTML(response.text)
    # frame_url = index_url + html.xpath('//div/@data-belt-path')[-1]
    # response = requests.get(frame_url)
    frame_url = ''
    soup = BeautifulSoup(response.text, "html.parser")
    urls = soup.findAll('div')
    for item in urls:
        if(item.get('data-belt-path')):
            frame_url = index_url + item.get('data-belt-path')
    response = requests.get(frame_url, headers=headers)
    lists(response.text, tab)

def main():
    tab_list = {
        'new-zealand': 'https://www.newshub.co.nz/home/new-zealand.html',
        'world': 'https://www.newshub.co.nz/home/world.html',
        'politics': 'https://www.newshub.co.nz/home/politics.html',
        'sports': 'https://www.newshub.co.nz/home/sport.html',
        # 'money': 'https://www.newshub.co.nz/home/money.html',

        # 'travel': 'https://www.newshub.co.nz/home/travel.html',
        # 'lifestyle': 'https://www.newshub.co.nz/home/entertainment/food-drink.html',
        # 'health': 'https://www.newshub.co.nz/home/health.html',
        # 'shows': 'https://www.newshub.co.nz/home/shows.html',
    }
    for tab, value in tab_list.items():
        get_html(value, tab)
    get_detail()


if __name__ == '__main__':
    main()
