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

# HOST= "130.61.52.228"
# DATABASE="tempnews"
# USER="tempnewsadmin"
# PASSWORD="FD32sd$7De9ds^&"

finshed_succes = 1
finshed_error = 9

conn = pymysql.connect( host=HOST, database=DATABASE, user= USER, password=PASSWORD, charset='utf8')
cursor = conn.cursor()

base_url = "https://www.bbc.com"

headers = {
    "accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36"
}
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='bbc.log',
                    filemode='w')
def get_hash():
    return str(uuid.uuid1()).replace("-", "")
#插入基本信息
def insert_nytimes(href, src, title, desc, k):
    href = base_url + href
    if deduplication_url(href) is None:
        sql = """
            insert into news(href, img_url, title, description, country, source, menu, href_hash) values(%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (href, src, title, desc,'uk', 'bbc', k, get_hash()))
        conn.commit()

#去重
def deduplication_url(url):
    sql = """
        select * from news where href = %s
    """
    cursor.execute(sql, (url))
    return cursor.fetchone()

#插入详情
def insert_details(news_id, content):
    sql = """
        insert into details(news_id, content) values(%s, %s)
    """
    cursor.execute(sql, (news_id, content))
    conn.commit()

#获取未爬取详情页的数据
def get_nytimes():
    sql = """
        select * from news where status = 0 and source = 'bbc'
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

#解析首页的json
def parse_first_json(content, k):
    json_text = json.loads(content)
    payload = json_text['payload'][0]
    if 200 == payload['meta']['responseCode']:
        results = payload['body']['results']
        for result in results:
            if 'url' not in result:
                continue
            href = result['url']
            title = result['title']
            image = result['image']
            src = image['href'] if image is not None else ''
            desc = result['summary']
            insert_nytimes(href, src, title, desc, k)
            logging.info("parse_first_json success, href = %s", href)

#解析详情页
def parse_detail_json(content, url, bbc_id):
    try:
        json_text = json.loads(content)
        detail_data = json_text['data']
        article_data = detail_data["article?currentPageAnalyticsDestination=NEWS_GNL&env=live&host=www.bbc.com&isAdvertisingEnabled=true&language=en-GB&uri=%2Fnews%2F" + (url.split("/")[-1])]
        data = article_data['data']
        blocks = data['blocks']
        content_list = []
        for block in blocks:
            if 'image' in block['type']:
                img_url = block['model']['media']['originalSrc']
                img_text = block['model']['media']['alt']
                imgtext = "<div class=\"imgText\">" + img_text + "</div>"
                content_list.append("<img src = '%s' class=\"abcImg\" />" % (img_url))
                content_list.append(imgtext)
            if 'text' in block['type']:
                text = block['model']['blocks'][0]['model']['text']
                content_list.append(text)
            if 'crosshead' in block['type']:
                head = block['text']
                h2 = "<div class=\"head3\">" + head + "</div>"
                content_list.append(h2)
        time.sleep(1)
        insert_details(bbc_id, json.dumps(content_list))
        update_nytimes(bbc_id, finshed_succes)
    except:
        update_nytimes(bbc_id, finshed_error)
        logging.info("parse_detail_json error, bbc_id = %s", bbc_id)

def parse_detail_html(content):
    soup = BeautifulSoup(content, "html.parser")
    scripts = soup.find_all("script")
    for script in scripts:
        if 'window.__INITIAL_DATA__=' in str(script):
            return str(script).split("window.__INITIAL_DATA__=")[1].split(";</script>")[0]

def parse_detail():
    bbc_list = get_nytimes()
    for bbc in bbc_list:
        json_content = parse_detail_html(request_details(bbc[1]))
        parse_detail_json(json_content, bbc[1], bbc[0])

def main():
    map_dict = {
        'uk':'uk-48270993',
        'business': 'business-47737521',
        'world': 'world-47639450',
        'world-asia': 'world-asia-47639453',
        'technology': 'technology-47078793',
        'science': 'science-environment-47179475',
        'arts': 'entertainment-arts-47639448',
    }
    for k,v in map_dict.items():
        url = "https://push.api.bbci.co.uk/batch?t=%2Fdata%2Fbbc-morph-lx-commentary-data-paged%2FassetUri%2Fnews%252Flive%252F"+ v +"%2FisUk%2Ffalse%2Flimit%2F20%2FnitroKey%2Flx-nitro%2FpageNumber%2F1%2Fversion%2F1.5.4?timeout=5"
        r = requests.get(url, headers = headers)
        parse_first_json(r.content, k)
        time.sleep(1)
    parse_detail()

if __name__ == '__main__':
    main()
