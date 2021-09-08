"""
    京东的抓包程序
    主要获取海鲜水产类商品数据
    起始页：https://www.jd.com/allSort.aspx
"""

import requests
from pyquery import PyQuery as pq
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import csv


"""
获取url指向的html页面数据
"""
def get_page(url):
    global TIMESLEEP
    global browser
    global wait

    browser.get(url)
    submit = wait.until(EC.presence_of_element_located((By.XPATH, '//div[contains(@class,"tab-main")]/ul/li[5]')))
    time.sleep(TIMESLEEP)

    # 向下滚动30屏，每屏50行
    for i in range(30):
        browser.execute_script("window.scrollBy(0,50)")
        time.sleep(0.1)
    submit.click()
    time.sleep(TIMESLEEP)
    return browser.page_source


"""
解析html页面
['品牌', '店铺名称', '商品名称', '商品现价', '活动信息', '规格', '累计评价']
"""
def parse_page(html, url):
    global fieldnames_merinfo

    doc = pq(html, parser='html')

    page_item = dict()
    page_item[fieldnames_merinfo[0]] = doc('div.detail > div.ETab > div.tab-con > div > div.p-parameter > ul > li > a').text()
    page_item[fieldnames_merinfo[1]] = doc('div.crumb-wrap div.contact.fr.clearfix div.J-hove-wrap.EDropdown.fr div.name a').text()
    page_item[fieldnames_merinfo[2]] = doc('div.itemInfo-wrap div.sku-name').text()
    page_item[fieldnames_merinfo[3]] = doc('div.itemInfo-wrap > div.summary.summary-first > div.summary-price-wrap > div.summary-price.J-summary-price span.p-price').text()
    page_item[fieldnames_merinfo[4]] = doc('div.itemInfo-wrap > div.summary.summary-first > div.summary-price-wrap > div.summary-top > div.summary-promotion > div.dd.J-prom-wrap.p-promotions-wrap > div.p-promotions > ins').text().strip()
    page_item[fieldnames_merinfo[5]] = doc('div.itemInfo-wrap > div.summary.p-choose-wrap #choose-attrs > div.li.p-choose div.dd i').text()
    page_item[fieldnames_merinfo[6]] = doc('#detail > div.tab-main.large > ul > li.current > s').text().replace('(', '').replace(')', '')
    return page_item


"""
爬取页面数据
"""
def crawl_all_page_url():
    global CATEGORY_NUM
    global TIMESLEEP
    global cookie_info
    global browser
    global wait

    browser.get('https://www.jd.com/allSort.aspx')

    # 写地址信息cookie
    for cookieeee in cookie_info:
        browser.add_cookie(cookie_dict=cookieeee)

    time.sleep(TIMESLEEP)

    browser.refresh()

    wait.until(EC.presence_of_element_located(
        (By.XPATH, '/html/body/div[5]/div[2]/div[1]/div[2]/div[2]/div[9]/div[2]/div[3]')))

    CASE = [] # 存储所有需要获取的特型数据
    for i in range(1):  # 海鲜水产
        initcase = '/html/body/div[5]/div[2]/div[1]/div[2]/div[2]/div[9]/div[2]/div[3]/dl[3]/dd/a[{}]'.format(i + 1)
        CASE.append(initcase)
    # 规则只要更改range里面的值和dl[]里面的值，可高度扩展

    for case in CASE:
        submit = browser.find_element_by_xpath(case)
        browser.execute_script("arguments[0].click();", submit)

        # selenium执行时并不会自动切换到新开的页签或者窗口上，还会停留在之前的窗口中，所以两次打印的句柄都一样。新开窗口后必须通过脚本来进行句柄切换，才能正确操作相应窗口中的元素
        handle = browser.current_window_handle
        handles = browser.window_handles
        
        for newhandle in handles:
            if newhandle != handle:
                browser.switch_to.window(newhandle)
        
        time.sleep(TIMESLEEP)

        wait.until(EC.presence_of_element_located((By.XPATH, '//div[@id="J_goodsList"]/ul[contains(@class,"gl-warp")]')))

        doc = pq(browser.page_source, parser='html')

        # 读取所有商品的连接
        for li in list(doc('div#J_goodsList ul.gl-warp li').items())[:CATEGORY_NUM]:
            merUrl = 'https:' + str(li('div div.p-commit strong a').attr('href')).replace('#comment', '')
            ALL_PAGE_URL.append(merUrl)

        time.sleep(TIMESLEEP)

        browser.close()
        browser.switch_to.window(handle)


"""
创建新的csv文件
"""
def csv_create():
    global FILENAME_MER
    global fieldnames_merinfo
    global ENCODING

    with open(FILENAME_MER, 'w', encoding=ENCODING, newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames_merinfo)


"""
将商品信息写入csv
"""
def save_csv_merinfo(item):
    global FILENAME_MER
    global fieldnames_merinfo
    global ENCODING

    with open(FILENAME_MER, 'a', encoding=ENCODING, newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames_merinfo)
        writer.writerow(item)


if __name__ == '__main__':

    # 用户自定义配置区********************************
    CATEGORY_NUM = 1  # 每个品类获取的商品数量，暂定100，想统计多少改这里就行（比如：鱼类，会获取100个商品）
    TIMESLEEP = 2   # 睡眠间隔
    FILENAME_MER = 'jd.csv'  # 商品信息的文件名
    ENCODING = 'UTF-8'  # 保存的CSV的编码
    fieldnames_merinfo = ['品牌', '店铺名称', '商品名称', '商品现价', '活动信息', '规格', '累计评价']  # csv文件的字段
    # 地址信息写入cookie，就可以获取某地区的商品列表了，改地址只需要改这里就行了（两个参数的value都需要对应着改）
    cookie_info = [
        {"name": "areaId", "value": "1", "domain": ".jd.com", 'path': '/', 'expires': None},
        {"name": "ipLoc-djd", "value": "1-72-2799-0", "domain": ".jd.com", 'path': '/', 'expires': None}
    ]
    # **********************************************

    # 计时器
    start = time.time()

    csv_create()  # 创建新csv写入数据

    # 去重
    URLSET = []  # 已存在的url的集合

    # 爬取商品信息
    ALL_PAGE_URL = []  # 所有的网页链接

    # browser = webdriver.PhantomJS()  # selenium模拟浏览器
    browser = webdriver.Chrome()

    wait = WebDriverWait(browser, 20)  # 等待20s浏览器驱动响应

    crawl_all_page_url()  # 抓商品链接

    for page_url in ALL_PAGE_URL:
        if page_url not in URLSET:
            URLSET.append(page_url)
            try:
                html = get_page(page_url)  # 请求网页，selenium动态渲染
                item_mer = parse_page(html, url=page_url)  # 解析网页

                # 一个网页的商品信息爬取完毕时，保存数据
                save_csv_merinfo(item_mer)  # 保存商品信息

            except Exception as error:
                print('网页请求发生错误{}>>>'.format(error))
        print('一个网页请求已经结束>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        time.sleep(TIMESLEEP)

    browser.close()

    end = time.time()
    print('总共用时{}秒'.format(end - start))
