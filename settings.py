#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: settings.py

Created on Mon Sep 23 21:06:33 2019

@author: qjfoidnh
"""

abs_path = "E:/spider/"
# 下载文件的目录，此处为Linux下目录格式，Windows需注意反斜杠转义问题。此目录必须事先建好，且最后一个‘/‘不能丢

current_path = "E:/spider/"
# 此目录代表项目代码的位置，不一定与上一个相同

# aria2配置
aria2url = "http://97.64.126.2:6800/jsonrpc"
aria2token = "5698d2d9d39e66efef79"

# 浏览器通用头部
head = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

cookie_raw_ehentai = "ipb_member_id=5238420; ipb_pass_hash=6465eb896997c6dbca6106e592f1fcbe; ipb_session_id=e09a93105c6a757749632d13d8ce0549; sk=h9z8x078ve0z4z84s284es5hmub2; s=e2c6ababf"
# 从浏览器里复制来的cookies大概就是这样的格式，exhentai同理

cookie_raw_exhentai = '''xxxxxxxx'''

# 代理地址，E站需要科kx学访问，此处仅支持http代理。关于代理的获得及设置请自行学习
# 听说现在不科学也可以了，如果属实，可令proxies = None
# proxies = {"http": "http://localhost:1086", "https": "http://localhost:1086"}
proxies = None


def cookieToDict(cookie):
    '''
    将从浏览器上Copy来的cookie字符串转化为Dict格式
    '''
    itemDict = {}
    items = cookie.split(';')
    for item in items:
        key = item.split('=')[0].replace(' ', '')
        value = item.split('=')[1]
        itemDict[key] = value
    return itemDict


def cookie_ehentai(address):
    if "e-hentai" in address:
        return cookieToDict(cookie_raw_ehentai)
    elif "exhentai" in address:
        return cookieToDict(cookie_raw_exhentai)
    else:
        return cookieToDict(cookie_raw_ehentai)
