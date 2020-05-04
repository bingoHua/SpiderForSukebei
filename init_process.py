#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: init_process.py

Created on Sun Sep 22 21:20:54 2019

@author: qjfoidnh
"""

from settings import *
from tools import Get_page, Download_img
from second_process import Ehentai
from checkdalive import removetask
from sql_module import mq
import time
import os


# 功能：尝试下载未完成列表里的图片到指定路径
def fixexcepts(itemid, img_urls, filepaths):
    img_urls_new = list()
    filepaths_new = list()
    img_urls = img_urls.split("Š")  # 从字符串还原回列表
    filepaths = filepaths.split("Š")
    for (imglink, path) in zip(img_urls, filepaths):
        try:
            content = Get_page(imglink, cookie=cookie_ehentai(imglink))
            if not content:
                img_urls_new.append(imglink)
                filepaths_new.append(path)
                continue
            time.sleep(10)
            try:
                img_src = content.select_one("#i7 > a").get('href')  # 高质量图
            except AttributeError:  # 如果高质量图没提供资源
                img_src = content.select_one("img[id='img']").get("src")  # 一般质量图
            src_name = content.select_one("#i2 > div:nth-of-type(2)").text.split("::")[0].strip()  # 图文件名
            raw_path = path
            if os.path.exists(raw_path + '/' + src_name):
                continue
            http_code = Download_img(img_src, raw_path + '/' + src_name, cookie=cookie_ehentai(imglink))
            if http_code != 200:
                raise Exception("Network error!")
        except Exception:
            img_urls_new.append(imglink)
            filepaths_new.append(path)
    result = mq.resetunfinish(itemid, img_urls_new, filepaths_new)
    return result


class DownEngine:
    def __init__(self):
        pass

    # 功能：根据传入地址，选择优先下载模式。获取资源标题，写入数据库，并调用次级处理模块
    def engineEhentai(self, address):
        if 'chmode' in address:
            mode = 'normal'
            removetask(address=address)
        else:
            mode = 'bt'
        address = address.replace('chmode', '')
        content = Get_page(address, cookie=cookie_ehentai(address))
        if not content:
            return 2
        warning = content.find('h1', text="Content Warning")
        # e站对部分敏感内容有二次确认
        if warning:
            address += '?nw=session'
            content = Get_page(address, cookie=cookie_ehentai(address))
            if not content:
                return 2
        title = content.select_one("h1[id='gj']").text
        if not len(title):  # 有些资源没有日文名，则取英文名
            title = content.select_one("h1[id='gn']").text
            if not len(title):
                return 2

        title = title.replace("'", '''"''')  # 含有单引号的标题会令sql语句中断
        title_st = mq.addcomicname(address, title)
        if type(title_st) == Exception:
            return title_st

        ehentai = Ehentai(address, title, mode=mode)
        result = ehentai.getOthers()
        return result