#coding:utf-8
import string

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver

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
DATABASE="tempnews"
USER="tempnewsadmin"
PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.abc.net.au/news/"
website = "https://www.abc.net.au"

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
        cursor.execute(sql, (href, src, title, desc,'au', 'abc', tab, get_hash()))
        conn.commit()


def deduplication_url(url):
    sql = """
        select * from nytimes where source='abc' and href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()



def insert_details(nytimes_id, figure, p_list, alt, src, content):
    sql = """
        insert into nytimes_details(nytimes_id, figure, p_list, alt, src, content) values(%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (nytimes_id, figure, p_list, alt, src, content))
    conn.commit()

def get_nytimes():
    sql = """
        select * from nytimes where status = 0 and source = 'abc'
    """
    cursor.execute(sql)
    return cursor.fetchall()


def update_nytimes(id):
    sql = "update nytimes set status = 1 where id = %s"
    cursor.execute(sql, (id))
    conn.commit()




def parse_top(html, tab, value):
    soup = BeautifulSoup(html, "html.parser")
    lists = soup.find("ul", attrs={'data-component':"List"})
    article_list = lists.find_all("li", {'data-component':"ListItem"})
    for article in article_list:
        try:
            head_a = article.find("a", attrs={'data-component':"Link"})
            href = website + head_a.get('href')
            imgs = article.find("img", {'data-component':"Image"}).get('src')
            parsed = urlparse(imgs)
            src =parsed.scheme +'://' + parsed.netloc + parsed.path
            title = article.h3.span.get_text()
            desc = article.find('div', {'data-component':"CardDescription"}).get_text()
            insert_nytimes(href, src, title, desc, value)
        except:
            logging.error("top parse error")



def request_details(href):
    r = requests.get(href, headers = headers)
    return r.content


def parse_list(html, tab, value):
    soup = BeautifulSoup(html, "html.parser")
    print(soup)
    tmp = soup.find("div", class_="site-content")
    print(tmp)
    if tmp:
        div_list = tmp.find_all("div", class_="section")
        print(div_list)
        for div in div_list:
            try:
                head_a = div.a.get('href')
                href = website + head_a
                tmp = div.find("div", class_='CtQll')
                imgs = tmp.find("img", {'data-component': "Image"}).get('data-src')
                parsed = urlparse(imgs)
                src = parsed.scheme + '://' + parsed.netloc + parsed.path
                title = div.find("span", {'data-component': "KeyboardFocus"}).get_text()
                desc = div.find("div", {'data-component': "CardDescription"}).get_text()
                # insert_nytimes(href, src, title, desc, value)
            except:
                logging.error('parase_list')


def parse_content():
    nytimes_list = get_nytimes()
    for nytimes in nytimes_list:
        try:
            content = []
            soup = BeautifulSoup(request_details(nytimes[1]), "html.parser")
            article = soup.find("div", id="body")
            tmp = article.find("div", {'data-component':"LayoutContainer"})
            decoy = tmp.find("p", class_="_1HzXw")
            lists = decoy.parent
            first = soup.find("img")
            imgs = first.get("data-src")
            alt = first.get("alt")
            parsed = urlparse(imgs)
            imgurl = parsed.scheme + '://' + parsed.netloc + parsed.path
            print(imgurl, alt)
            for item in lists:
                try:
                    if "p" == item.name:
                        content.append(item.get_text())
                    elif "h2" == item.name:
                        h2 = "<div class=\"head3\">"+ item.get_text() +"</div>"
                        content.append(h2)
                    elif "figure" == item.name:
                        figure = item.find("img")
                        imgs = figure.get("data-src")
                        parsed = urlparse(imgs)
                        src = parsed.scheme + '://' + parsed.netloc + parsed.path
                        htmlimg = "<img src=\""+src+"\" class=\"abcImg\"></img>"
                        content.append(htmlimg)
                        imgtext = item.find('figcaption').get_text()
                        if imgtext:
                           text = "<div class=\"imgText\">" + imgtext + "</div>"
                           content.append(text)
                except:
                    logging.error("aaaabbb")
            insert_details(nytimes[0], first, lists, alt, imgurl,  json.dumps(content))
        except:
            logging.error("content parse error, id = %s" % nytimes[0])
        update_nytimes(nytimes[0])

def select_all_nytimes():
    sql = """
        select * from nytimes
    """
    cursor.execute(sql)
    return cursor.fetchall()


def get_page_sourse(url):
    browser = webdriver.Chrome()
    browser.get(url)
    page_sourse = browser.page_source
    browser.close()
    return page_sourse

def main():
    tab_list = {
        'europe': 'https://www.thelocal.com/latest-news-from-europe-in-english/?sckattempt=1'
    }



    for tab, value in tab_list.items():
        url = value
        url = 'https://www.weiney.com/'
        browser = get_page_sourse(url)
        print(browser)
        # r = requests.get(url, headers=headers)
        # parse_list(r.content, tab, value)
        # time.sleep(1)
    # parse_content()


if __name__ == '__main__':
    main()

