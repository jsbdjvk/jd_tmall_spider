"""
    天猫的抓包程序
    主要获取甄选全球鲜果页面数据
    起始页：https://miao.tmall.com/
"""

import requests
from pyquery import PyQuery as pq
import time
import csv
import pycurl
from io import BytesIO
import certifi
import json
from urllib import parse


"""
提取商品id
"""
def getMerId(url):
    params = parse.parse_qs(parse.urlparse(url).query)
    return params['id'][0]


"""
通过商品id获取商品信息
['品牌', '商品名称', '商品原价', '商品现价', '规格', '月销量', '累计评价']
"""
def get_tmall_info(mer_id):
    global TIMESLEEP
    global fieldnames_merinfo

    t = int(time.time() * 1000)

    url = 'https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/' \
          '?jsv=2.4.8&appKey=12574478&t={}' \
          '&sign=7c9e1dedaa295fdb175d22c99746493b&api=mtop.taobao.detail.getdetail' \
          '&v=6.0&dataType=jsonp&ttid=2017%40taobao_h5_6.6.0&AntiCreep=true&type=jsonp&callback=mtopjsonp2&' \
          'data=%7B%22itemNumId%22%3A%22{}%22%7D'.format(t, mer_id)

    headers = {'Accept': '*/*',
               'Accept-Language': 'zh-CN',
               'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) AppleWebKit/603.3.8 (KHTML, like Gecko) FxiOS/10.6b8836 Mobile/14G60 Safari/603.3.8',
               'Referer': 'https://detail.m.tmall.com/item.htm?spm=a220m.6910245.0.0.55b17434eiwv4f&id={}'.format(mer_id)
               }

    response = requests.get(url, headers=headers)

    merData = json.loads(response.text.lstrip('mtopjsonp2(').rstrip(')'))['data']

    if 'item' not in merData.keys():
        return False

    otherInfo = json.loads(merData['apiStack'][0]['value'])

    page_item = dict()

    for x in merData['props']['groupProps']:
        if '基本信息' in x.keys():
            for y in x['基本信息']:
                if '品牌' in y.keys():
                    page_item[fieldnames_merinfo[0]] = y['品牌']
                if '净含量' in y.keys():
                    page_item[fieldnames_merinfo[4]] = y['净含量']

    if 'newExtraPrices' in otherInfo['price'].keys():
        page_item[fieldnames_merinfo[2]] = otherInfo['price']['newExtraPrices'][0]['priceText']
    else:
        page_item[fieldnames_merinfo[2]] = otherInfo['price']['price']['priceText']

    page_item[fieldnames_merinfo[1]] = merData['item']['title']
    page_item[fieldnames_merinfo[3]] = otherInfo['price']['price']['priceText']
    page_item[fieldnames_merinfo[5]] = otherInfo['item']['sellCount']
    page_item[fieldnames_merinfo[6]] = merData['item']['commentCount']

    print(page_item)

    time.sleep(TIMESLEEP)

    return page_item


"""
爬取页面数据
"""
def crawl_all_page_url():
    global CATEGORY_NUM
    global TIMESLEEP

    crl = pycurl.Curl()
    crl.setopt(pycurl.CAINFO, certifi.where())
    crl.setopt(pycurl.USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.17 Safari/537.36')
    buff = BytesIO()
    crl.setopt(pycurl.URL, "https://miao.tmall.com/")
    crl.setopt(crl.WRITEFUNCTION, buff.write)
    crl.perform()
    html = buff.getvalue()
    crl.close()

    doc = pq(html, parser='html')

    fruits = json.loads(doc("div.mui-zebra-page > div:nth-child(12) .J_dynamic_data").text())['items']

    # 读取所有商品的连接
    for fruit in fruits:
        merUrl = 'https:' + fruit["itemUrl"]
        ALL_PAGE_URL.append(merUrl)

    time.sleep(TIMESLEEP)


"""
创建新的csv文件
"""
def csv_create():
    global FILENAME_MER
    global fieldnames_merinfo

    with open(FILENAME_MER, 'w', encoding=ENCODING, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames_merinfo)


"""
将商品信息写入csv
"""
def save_csv_merinfo(item):
    global FILENAME_MER
    global fieldnames_merinfo

    with open(FILENAME_MER, 'a', encoding=ENCODING, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_merinfo)
        writer.writerow(item)


if __name__ == '__main__':

    # 用户自定义配置区********************************
    CATEGORY_NUM = 12  # 每个品类获取的商品数量，暂定100，想统计多少改这里就行（比如：鱼类，会获取100个商品）
    TIMESLEEP = 2   # 睡眠间隔
    FILENAME_MER = 'tmall.csv'  # 商品信息的文件名
    ENCODING = 'UTF-8'  # 保存的CSV的编码
    fieldnames_merinfo = ['品牌', '商品名称', '商品原价', '商品现价', '规格', '月销量', '累计评价']  # csv文件的字段
    # **********************************************

    # 计时器
    start = time.time()

    csv_create()  # 创建新csv写入数据

    # 去重
    URLSET = []  # 已存在的url的集合

    # 爬取商品信息
    ALL_PAGE_URL = []  # 所有的网页链接
    crawl_all_page_url()  # 抓商品链接

    for page_url in ALL_PAGE_URL:
        if page_url not in URLSET:
            URLSET.append(page_url)
            try:
                mer_id = getMerId(page_url)  # 获取商品id
                item_mer = get_tmall_info(mer_id)  # 获取商品信息
                if False == item_mer:
                    print("商品下架或者不存在")
                    continue

                # 一个网页的商品信息爬取完毕时，保存数据
                save_csv_merinfo(item_mer)  # 保存商品信息

            except Exception as error:
                print('网页请求发生错误{}>>>'.format(error))
        print('一个网页请求已经结束>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        time.sleep(TIMESLEEP)

    end = time.time()
    print('总共用时{}秒'.format(end - start))