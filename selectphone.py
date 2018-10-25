# !usr/bin/env python3
# encoding:utf-8
"""
@project = selectphone
@file = selectphone
@author = 'Easton Liu'
@creat_time = 2018/10/8 17:51
@explain:爬取京东商城所有手机价格和配置信息，并写入到MongoDB中

"""
import requests
import re
import pymongo
import json
from lxml import etree

DB = "cellphone"
def fix_url(string):
    if re.match(r"http://",string):
        return string
    if re.match(r"//",string):
        return "http:"+string

def get_page_num():
    url = r"https://list.jd.com/list.html?cat=9987,653,655"
    rec = requests.get(url).text
    s = etree.HTML(rec)
    page_nodes = s.xpath('//span[@class="p-num"]/a')
    for node in page_nodes:
        if node.attrib["class"]=='':
            page_num = int(node.text)
            return page_num

def get_price(skuid):
    url = r'https://c0.3.cn/stock?skuId='+str(skuid)+r'&area=1_72_4137_0&venderId=1000004123&cat=9987,653,655&buyNum=1' \
          r'&choseSuitSkuIds=&extraParam={%22originid%22:%221%22}&ch=1&fqsp=0&pduid=15275638276571783045943&pdpin=' \
          r'&detailedAdd=null&callback=jQuery2254662'
    rec = requests.get(url).text
    matched = re.search('jQuery\d+\((.+)\)',rec)
    if matched:
        data = json.loads(matched.group(1))
        price = data["stock"]["jdPrice"]["p"]
        return price
    return 0

def get_item(skuid,url):
    price = get_price(skuid)
    rec = requests.get(url).text
    s = etree.HTML(rec)
    nodes = s.xpath('//div[@class="Ptable-item"]')
    params = {"price":price,"skuid":skuid}
    for node in nodes:
        text_nodes=node.xpath("./dl")[0]
        k = ""
        v = ""
        for text_node in text_nodes:
            if text_node.tag == "dt":
                k = text_node.text
            elif text_node.tag == "dd" and "class" not in text_node.attrib:
                v = text_node.text
            params[k] = v
    return params

def get_cellphone(db,page):
    url = r'https://list.jd.com/list.html?cat=9987,653,655&page={}&sort=sort_rank_asc&trans=1&JL=6_0_0#J_main'.format(page)
    rec = requests.get(url).text
    s = etree.HTML(rec)
    phone_nodes = s.xpath('.//div[@class="p-img"]/a')
    for node in phone_nodes:
        item_url = fix_url(node.attrib['href'])
        matched = re.search('item\.jd\.com/(\d+)\.html',item_url)
        skuid = matched.group(1)
        saved = db.items.find({"skuid":skuid}).count()
        if saved > 0:
            print(skuid)
            continue
        item = get_item(skuid,item_url)
        db.items.insert(item)

if __name__=="__main__":
    client = pymongo.MongoClient()
    db = client[DB]
    db.items.remove({})
    page_num = get_page_num()
    for i in range(page_num):
        get_cellphone(db,i+1)
