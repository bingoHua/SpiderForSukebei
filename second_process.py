#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: second_process.py

Created on Mon Sep 23 20:35:48 2019

@author: qjfoidnh
"""

import time
import datetime
import requests
from tools import Get_page, Download_img, postorrent
from checkdalive import getinfos
from settings import proxies
from settings import *
import re
import os
from logger_module import logger

formatted_today=lambda:datetime.date.today().strftime('%Y-%m-%d')+'/' #返回当前日期的字符串，建立文件夹用


#功能：处理资源标题里一些可能引起转义问题的特殊字符
def legalpath(path):
    path = list(path)
    path_raw = path[:]
    for i in range(len(path_raw)):
        if path_raw[i] in [' ','[',']','(',')','/','\\']:
            path[i] = '\\'+ path[i]
        elif path_raw[i]==":":
            path[i] = '-'
    return ''.join(path)

class Ehentai(object):
    def __init__(self, address, comic_name, mode='normal'):
        self.head = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                     'accept-encoding': 'gzip, deflate, br',
                     'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                     'upgrade-insecure-requests': '1',
                     'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
                     }
        self.address = address
        self.mode = mode
        self.gid = address.split('/')[4]
        self.tid = address.split('/')[5]
        self.content = Get_page(address, cookie=cookie_ehentai(address))
        self.comic_name = legalpath(comic_name)
        self.raw_name = comic_name.replace("/"," ")
        self.raw_name = self.raw_name.replace(":","-")
        self.src_list = []
        self.path_list = []
    
    #功能：下载的主功能函数    
    def getOthers(self):
        if not self.content:
            return 2
        today = formatted_today()
        logger.info("E-hentai: %s start!" %self.raw_name)
        complete_flag = True
        pre_addr = re.search(r'(e.+org)', self.address).group(1)
        if self.mode=='bt': #bt种子模式
            content = Get_page("https://%s/gallerytorrents.php?gid=%s&t=%s"%(pre_addr,self.gid,self.tid), cookie=cookie_ehentai(self.address))
            torrents = content.find_all(text="Seeds:")
            if not torrents:
                self.mode = 'normal' #图片下载模式
            else:
                torrents_num = [int(tag.next_element) for tag in torrents]
                target_index = torrents_num.index(max(torrents_num))
                torrent_link = content.select('a')[target_index].get('href')
                torrent_name = content.select('a')[target_index].text.replace('/',' ')
            
                #e-hentai与exhentai有细微差别
                if 'ehtracker' in torrent_link:
                    req = requests.get(torrent_link)
                    if req.status_code==200:
                        with open(torrent_name+'.torrent', 'wb') as ft:
                            ft.write(req.content)
                    id = postorrent(torrent_name+'.torrent', dir=abs_path+today)
                    if id: 
                        filepath = getinfos().get(id).get('filepath')
                        return {'taskid':id, 'filepath':filepath}
                    else: self.mode = 'normal'
                
                #e-hentai与exhentai有细微差别
                elif 'exhentai' in torrent_link:

                    req = requests.get(torrent_link, headers={'Host': 'exhentai.org',
                                                              'Referer': "https://%s/gallerytorrents.php?gid=%s&t=%s"%(pre_addr,self.gid,self.tid),
                                                              'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'}, 
                                                              cookies=cookie_ehentai(self.address), proxies=proxies)
                    if req.status_code==200:
                        with open(abs_path+'bttemp/'+torrent_name+'.torrent', 'wb') as ft:
                            ft.write(req.content)
                        id = postorrent(abs_path+'bttemp/'+torrent_name+'.torrent', dir=abs_path+today)
                        if id: 
                            filepath = getinfos().get(id).get('filepath')
                            return {'taskid':id, 'filepath':filepath}
                        else:
                            self.mode = 'normal'
                    else:
                        self.mode = 'normal'
                    
        page_tag1 = self.content.select_one(".ptds")
        page_tags = self.content.select("td[onclick='document.location=this.firstChild.href']")
        indexslen = len(page_tags)//2-1
        if indexslen <=0:
            indexslen = 0
        pagetags = page_tags[0:indexslen]
        pagetags.insert(0, page_tag1)
        
        #有些页面图片超过8页，页面直接链接可能获取不全，采用按规则生成链接方法
        last_page = pagetags[-1]
        last_link = last_page.a.get('href')
        page_links = [pagetag.a.get('href') for pagetag in pagetags]
        try:
            last_number = int(re.findall(r'\?p=([0-9]+)',last_link)[0])
        except IndexError: 
            pass #说明本子较短，只有一页，不需做特别处理
        else:
            if last_number>=8:
                templete_link = re.findall(r'(.+\?p=)[0-9]+',last_link)[0]
                page_links = [templete_link+str(page+1) for page in range(last_number)]
                page_links.insert(0, page_tag1.a.get('href'))
            
        for page_link in page_links:
            content = Get_page(page_link, cookie=cookie_ehentai(self.address))
            if not content:
                return 2
            imgpage_links = content.select("div[class='gdtm']") #一种定位标签
            if not imgpage_links:
                imgpage_links = content.select("div[class='gdtl']") #有时是另一种标签
            for img_page in imgpage_links:
                try:
                    imglink = img_page.div.a.get('href') #对应第一种
                except:
                    imglink = img_page.a.get('href') #对应第二种
                content = Get_page(imglink, cookie=cookie_ehentai(self.address))
                if not content:
                    complete_flag = False
                    self.src_list.append(imglink)
                    self.path_list.append(abs_path+today+self.raw_name)
                    continue
                try:
                    img_src = content.select_one("#i7 > a").get('href') #高质量图
                except AttributeError:
                    img_src = content.select_one("img[id='img']").get("src") #小图
                src_name = content.select_one("#i2 > div:nth-of-type(2)").text.split("::")[0].strip() #图文件名
                raw_path = abs_path+today+self.raw_name
                try:
                    os.makedirs(raw_path)
                except FileExistsError:
                    pass
                if os.path.exists(raw_path+'/'+src_name):
                    continue
                http_code = Download_img(img_src, raw_path+'/'+src_name, cookie=cookie_ehentai(self.address))
                if http_code!=200:
                    time.sleep(10)
                    complete_flag = False
                    self.src_list.append(imglink)
                    self.path_list.append(raw_path)
                    continue
                else:
                    time.sleep(10)
        if not complete_flag:
            logger.warning("E-hentai: %s ONLY PARTLY finished downloading!" %self.raw_name)
            return (self.src_list, self.path_list)
            
        else:
            logger.info("E-hentai: %s has COMPLETELY finished downloading!" %self.raw_name)
            return 1