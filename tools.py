#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: tools.py

Created on Mon Sep 23 20:57:31 2019

@author: qjfoidnh
"""


import requests
import time
from bs4 import BeautifulSoup as Bs
from settings import head, aria2url, aria2token
from settings import proxies
import json
import base64
from pyaria2 import Aria2RPC

# 功能：对requets.get方法的一个封装，返回Bs对象
def Get_page(page_address, headers={}, cookie=None):
    pic_page = None
    innerhead = head.copy()
    innerhead.update(headers)
    try:
        pic_page = requests.get(page_address, headers=innerhead, proxies=proxies, cookies=cookie, verify=False)
    except Exception as e:
        return None
    if not pic_page:
        return None
    pic_page.encoding = 'utf-8'
    text_response = pic_page.text
    content = Bs(text_response, 'html.parser')
    
    return content

#功能：把种子文件发给Aria2服务，文件以base64编码
def postorrent(path, dir):
    with open(path, 'rb') as f:
        b64str = str(base64.b64encode(f.read()), 'utf-8')
    url = aria2url
    id_str = "AriaNg_%s_0.043716476479668254"%str(int(time.time())) #这个字符串可以随便起，只要能保证每次调用生成时不重复就行
    id = str(base64.b64encode(id_str.encode('utf-8')), 'utf-8').strip('=')
    req = requests.post(url, data=json.dumps({"jsonrpc":"2.0","method":"aria2.addTorrent","id":id,"params":["token:"+aria2token, b64str,[],{'allow-overwrite':"true"}]}))
    if req.status_code==200:
        return req.json().get('result')
    else:
        return False

# 功能：下载图片文件
def Download_img(page_address, filepath, cookie=None):

    try:
        pic_page = requests.get(page_address, headers=head, proxies=proxies, cookies=cookie, timeout=8, verify=False)
        if pic_page.status_code==200:
            pic_content = pic_page.content
            with open(filepath, 'wb') as file:
                file.write(pic_content)
        return pic_page.status_code
    except Exception as e:
        return e