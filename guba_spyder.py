"""
Created on Thurs Jan 19 16:10:21 2023

@author: 羚羊
"""
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from lxml import etree
import csv
import pandas as pd
import re


def get_referer(div):
    '''
    取得最终评论页面的地址
    :param div: 主页面div元素
    :return: 最终评论页面的地址
    '''
    # 首页获取的帖子网址有两种形式，如果是以news开头，则已经是最后的网址，如果不是，则要多做一步获得最后网址
    if div.xpath('./span[3]/a/@href')[0][1:5:] == 'news':
        detail_url = 'https://guba.eastmoney.com' + div.xpath('./span[3]/a/@href')[0]
        return detail_url
    else:
        detail_url = 'https:' + div.xpath('./span[3]/a/@href')[0]
        bro.get(detail_url)  # 打开页面
        response = bro.page_source
        tree = etree.HTML(response)
        try:
            comment_url = 'https:' + tree.xpath('//div[@class="bottom_btns clearfix"]/a/@href')[0]
            try:
                if tree.xpath('//div[@class="bottom_btns clearfix"]/@style')[0] == 'display: none;':
                    comment_url = detail_url
            except:
                if len(comment_url) < 30:
                    comment_url = detail_url
                comment_url = comment_url
        except:
            comment_url = detail_url
        return comment_url


def get_content_guba(url):
    '''
    获取网址开头为“guba”帖子内容与时间
    :param url: 帖子网址
    :return: 帖子内容与时间
    '''
    l = []
    bro.get(url)  # 打开页面
    response = bro.page_source
    tree = etree.HTML(response)
    try:
        try:
            time = tree.xpath('//*[@id="line2"]/div[1]/span[2]/text()')[0]
        except:
            time = tree.xpath('//*[@id="zwconttb"]/div[2]/text()')[0].strip()[4:-6:]
    except:
        time = ''
    l.append(time)
    try:
        content = tree.xpath('//*[@id="zwconbody"]/div//text()')
        content = ','.join(content)
        content = process_gbk(content)
    except:
        content = ''
    l.append(content)
    return l


def get_content_caifuhao(url):
    '''
    获取网址开头为“caifuhao”帖子内容与时间
    :param url: 帖子网址
    :return: 帖子内容与时间
    '''
    l = []
    bro.get(url)  # 打开页面
    response = bro.page_source
    tree = etree.HTML(response)
    try:
        time = tree.xpath('//*[@id="main"]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/span[2]/text()')[0]
    except:
        time = ''
    l.append(time)
    try:
        content = tree.xpath('//*[@id="main"]/div[2]/div[1]/div[1]/div[1]/div[3]/div[1]//text()')
        content = ','.join(content)
        content = process_gbk(content)
    except:
        content = ''
    l.append(content)
    return l


def get_comments(referer, postid, writer, data_info):
    '''
    获取帖子网址开头为"guba"的评论
    :param referer: 评论所在网址
    :param postid: 帖子的postid
    :param writer: 要写入的文件
    :param data_info: 用于作为帖子第一条记录的标题、内容、发布者等信息
    :return:
    '''
    referer = referer
    headers_comments = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Content-Length': '122',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': 'qgqp_b_id=02219768835ea8d780485368a0c72c3d; st_si=03840835922058; st_asi=delete; st_pvi=66677116630513; st_sp=2023-01-17%2011%3A45%3A16; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=60; st_psi=20230119185641946-117001300541-9828226267',
        'Host': 'guba.eastmoney.com',
        'Origin': 'https://guba.eastmoney.com',
        'Referer': referer,
        'sec-ch-ua': '"Not_A Brand";v="99", "Microsoft Edge";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.55',
        'X-Requested-With': 'XMLHttpRequest'
    }
    page = 1
    param = f'postid={postid}&sort=1&sorttype=1&p={page}&ps=30'
    payload = {
        'param': param,
        'path': 'reply/api/Reply/ArticleNewReplyList',
        'env': '2'
    }
    comment_url = 'https://guba.eastmoney.com/interface/GetData.aspx?path=reply/api/Reply/ArticleNewReplyList'
    # 使用post方法获取存有评论的json数据
    response = requests.post(comment_url, headers=headers_comments, data=payload)
    # 当response.json()['re']有内容时，循环一直进行，获取评论
    count = 1
    while response.json()['re']:
        param = f'postid={postid}&sort=1&sorttype=1&p={page}&ps=30'
        payload = {
            'param': param,
            'path': 'reply/api/Reply/ArticleNewReplyList',
            'env': '2'
        }
        response = requests.post(comment_url, headers=headers_comments, data=payload)
        re_list = response.json()['re']
        for re in re_list:
            # 如果这条评论的回复数大于2，则调用获取回复方法
            if int(re['reply_count']) > 2:
                replyid = re['reply_id']
                get_reply(referer, postid, replyid, writer, data_info, count)
                count += 1
            else:
                # 如果count=1，则表示这是帖子的第一条评论，则写入时要将评论与帖子信息一起写入，否则只写入评论
                if count == 1:
                    data_info['comment'] = process_gbk(re['reply_text'])
                    writer.writerow(data_info)
                    # 获取这条评论的回复
                    get_child_comments(re, writer)
                else:
                    data_comment = {
                        'title': '',
                        'author': '',
                        'read': '',
                        'comment_number': '',
                        'time': '',
                        'content': '',
                        'comment': process_gbk(re['reply_text'])
                    }
                    writer.writerow(data_comment)
                    get_child_comments(re, writer)
            count += 1
        page += 1


def get_comments_caifuhao(url, postid, writer, data_info):
    '''
    获取帖子网址开头为"caifuhao"的评论
    :param url: 评论所在网址
    :param postid: 帖子的postid
    :param writer: 要写入的文件
    :param data_info: 用于作为帖子第一条记录的标题、内容、发布者等信息
    :return:
    '''
    # 网址为开头为”caifuhao“的帖子无法通过post获取json数据来获取评论，因此通过selenium来获取评论
    bro.get(url)  # 打开页面
    response = bro.page_source
    tree = etree.HTML(response)
    div_list = tree.xpath('//*[@id="comment_all_content"]/div/div')
    count = 1
    try:
        for div in div_list:
            comment = process_gbk(div.xpath('./div/div[2]/div[2]/text()')[0])
            # 如果这条评论的回复数大于2，则调用获取回复方法
            if int(div.xpath('./@data-reply_count')[0]) > 2:
                replyid = div.xpath('./@data-reply_id')[0]
                get_reply(url, postid, replyid, writer, data_info, count)
                count += 1
            elif int(div.xpath('./@data-reply_count')[0]) == 0:
                if count == 1:
                    data_info['comment'] == comment
                    writer.writerow(data_info)
                else:
                    data_comment = {
                        'title': '',
                        'author': '',
                        'read': '',
                        'comment_number': '',
                        'time': '',
                        'content': '',
                        'comment': comment.replace(u'\xa0', u'')
                    }
                    writer.writerow(data_comment)
            else:
                if count == 1:
                    data_info['comment'] == comment
                    writer.writerow(data_info)
                else:
                    data_comment = {
                        'title': '',
                        'author': '',
                        'read': '',
                        'comment_number': '',
                        'time': '',
                        'content': '',
                        'comment': comment
                    }
                    writer.writerow(data_comment)
                    reply_list = div.xpath('./div/div[5]/div[2]')
                    for reply in reply_list[0:-2:]:
                        reply_comment = reply.xpath('./div/span[@class="l2_short_text"]/text()')[0]
                        data_reply = {
                            'title': '',
                            'author': '',
                            'read': '',
                            'comment_number': '',
                            'time': '',
                            'content': '',
                            'comment': process_gbk(reply_comment)
                        }
                        writer.writerow(data_reply)
            count += 1
    except:
        writer.writerow(data_info)


def get_reply(referer, postid, replyid, writer, data_info, count):
    '''
    获取评论下面的回复
    :param referer: 评论所在网址
    :param postid: 帖子的postid
    :param replyid: 回复的评论所对应的replyid
    :param writer: 要写入的文件
    :param data_info: 用于作为帖子第一条记录的标题、内容、发布者等信息
    :param count: 用于确认是否是帖子第一条回复的计数变量
    :return:
    '''
    referer = referer
    headers_reply = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive',
            'Content-Length': '144',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'qgqp_b_id=02219768835ea8d780485368a0c72c3d; st_si=03840835922058; st_asi=delete; st_pvi=66677116630513; st_sp=2023-01-17%2011%3A45%3A16; st_inirUrl=https%3A%2F%2Fwww.baidu.com%2Flink; st_sn=63; st_psi=20230119214823454-117001300541-1526738941',
            'Host': 'guba.eastmoney.com',
            'Origin': 'https://guba.eastmoney.com',
            'Referer': referer,
            'sec-ch-ua': '"Not_A Brand";v="99", "Microsoft Edge";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.55',
            'X-Requested-With': 'XMLHttpRequest'
        }
    p = 1
    param = f'postid={postid}&replyid={replyid}&sort=1&sorttype=1&ps=10&p={p}'
    payload = {
        'param': param,
        'path': 'reply/api/Reply/ArticleReplyDetail',
        'env': '2'
    }
    reply_url = 'https://guba.eastmoney.com/interface/GetData.aspx?path=reply/api/Reply/ArticleReplyDetail'
    # 同样，通过post方法获取带有回复的json数据来获取回复
    response = requests.post(reply_url, headers=headers_reply, data=payload)
    flag = True
    while response.json()['re']['child_replys']:
        param = f'postid={postid}&replyid={replyid}&sort=1&sorttype=1&ps=10&p={p}'
        payload = {
            'param': param,
            'path': 'reply/api/Reply/ArticleReplyDetail',
            'env': '2'
        }
        response = requests.post(reply_url, headers=headers_reply, data=payload)
        re = response.json()['re']
        if count == 1:
            # 如果这个回复所对应的评论还未写入，则先写入这条评论，再写入回复
            if flag:
                data_info['comment'] = process_gbk(re['reply_text'])
                writer.writerow(data_info)
                flag = False
            get_child_comments(re, writer)
        else:
            if flag:
                data_comment = {
                    'title': '',
                    'author': '',
                    'read': '',
                    'comment_number': '',
                    'time': '',
                    'content': '',
                    'comment': process_gbk(re['reply_text'])
                }
                writer.writerow(data_comment)
                flag = False
            get_child_comments(re, writer)
        count += 1
        p += 1


def get_child_comments(re, writer):
    '''
    获取回复下的子回复
    :param re: 子回复列表
    :param writer: 要写入的文件
    :return:
    '''
    for child in re['child_replys']:
        data_comment = {
            'title': '',
            'author': '',
            'read': '',
            'comment_number': '',
            'time': '',
            'content': '',
            'comment': process_gbk(child['reply_text'])
        }
        writer.writerow(data_comment)


def process_gbk(content):
    '''
    去掉无法识别的字符
    :param content: 要处理的内容
    :return: 处理后的内容
    '''
    content = re.sub(u'([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b])', '', content)
    return content


if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36'
    }
    # 实现无可视化界面的操作（无头浏览器）
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    # 不加载图片
    chrome_options.add_argument('blink-settings=imagesEnabled=false')
    # requests不能正常获取到页面元素，所以用selenium库
    bro = webdriver.Chrome(executable_path=r'D:\一些资料\一些编程文件\爬虫\selenium\chromedriver_win32\chromedriver.exe'
                           , options=chrome_options
                           )
    codes = pd.read_excel('../Code_1.xlsx', dtype='object')
    for code in codes['Code']:
        # 定义csv字段，存储评论信息至comments/股票代码.csv
        filepath = f'../comments/{code}.csv'
        csvf = open(filepath, 'a+', newline='', encoding='gb18030', errors='ignore')
        fieldnames = ['title', 'author', 'read', 'comment_number', 'time', 'content', 'comment']
        writer = csv.DictWriter(csvf, fieldnames=fieldnames)
        writer.writeheader()
        url = f'http://guba.eastmoney.com/list,{code}.html'
        bro.get(url)  # 打开页面
        response = bro.page_source
        tree = etree.HTML(response)
        page_num = tree.xpath('//div[@class="pager"]/span/span/span[1]/span/text()')[0]

        for i in range(1, int(page_num) + 1):
            page_url = f'http://guba.eastmoney.com/list,{code}_{i}.html'
            bro.get(page_url)  # 打开页面
            page_response = bro.page_source
            page_tree = etree.HTML(page_response)
            div_list = page_tree.xpath('//*[@id="articlelistnew"]/div')
            for div in div_list[1:-2:]:
                # 获取帖子标题、作者等信息
                try:
                    title = div.xpath('./span[3]/a/@title')[0]
                except:
                    title = ''
                try:
                    author = div.xpath('./span[4]/a/text()')[0]
                except:
                    author = ''
                try:
                    read = div.xpath('./span[1]/text()')[0]
                except:
                    read = ''
                try:
                    comment_number = div.xpath('./span[2]/text()')[0]
                except:
                    comment_number = ''
                data_info = {
                    'title': title,
                    'author': author,
                    'read': read,
                    'comment_number': comment_number,
                    'time': '',
                    'content': '',
                    'comment': ''
                }
                # 获取帖子最终网址
                referer = get_referer(div)
                # postid有两种不同存在方式
                try:
                    postid = div.xpath('./span[3]/a/@data-postid')[0]
                except:
                    postid = div.xpath('./span[3]/a/@href')[0][13:-5:]
                # 根据最后评论所在的网址类型调用不同的方法
                if referer[8:12:] == 'guba':
                    # 获取帖子内容
                    temp = get_content_guba(referer)
                    data_info['time'] = temp[0]
                    data_info['content'] = temp[1]
                    # 判断，如果帖子评论数为0，则不需要调用获取评论方法
                    if int(div.xpath('./span[2]/text()')[0]) == 0:
                        writer.writerow(data_info)
                    else:
                        get_comments(referer, postid, writer, data_info)
                elif referer[8:16:] == 'caifuhao':
                    temp = get_content_caifuhao(referer)
                    data_info['time'] = temp[0]
                    data_info['content'] = temp[1]
                    if int(div.xpath('./span[2]/text()')[0]) == 0:
                        writer.writerow(data_info)
                    else:
                        get_comments_caifuhao(referer, postid, writer, data_info)
                # 有些帖子是视频，遇到直接跳过
                else:
                    continue
                print(div.xpath('./span[3]/a/@title')[0], '写入成功！！！')
        print(filepath, '写入完成！！！')
        print('===============================================================================')
        # 关闭csv
        csvf.close()
