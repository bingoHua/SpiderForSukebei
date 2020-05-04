#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: checkdalive.py

Created on Mon Sep 23 21:20:09 2019

@author: qjfoidnh
"""

import os
from settings import current_path
os.chdir(current_path)
from sql_module import mq
import requests
from settings import aria2url, aria2token
import time
import json
import base64
import zipfile
import filetype

# 功能：向Aria2发送查询请求
def getinfos():
    id_str = "AriaNg_%s_0.043716476479668254"%str(int(time.time())) #随机生成即可，不用遵循一定格式
    id = str(base64.b64encode(id_str.encode('utf-8')), 'utf-8')
    id_str2 = "AriaNg_%s_0.053716476479668254"%str(int(time.time()))
    id2 = str(base64.b64encode(id_str2.encode('utf-8')), 'utf-8')
    data = json.dumps({"jsonrpc":"2.0","method":"aria2.tellActive","id":id,"params":["token:%s"%aria2token,["gid","totalLength","completedLength","uploadSpeed","downloadSpeed","connections","numSeeders","seeder","status","errorCode","verifiedLength","verifyIntegrityPending","files","bittorrent","infoHash"]]})
    data2 = json.dumps({"jsonrpc":"2.0","method":"aria2.tellWaiting","id":id2,"params":["token:%s"%aria2token,0,1000,["gid","totalLength","completedLength","uploadSpeed","downloadSpeed","connections","numSeeders","seeder","status","errorCode","verifiedLength","verifyIntegrityPending","files","bittorrent","infoHash"]]})
    req = requests.post(aria2url, data)
    req2 = requests.post(aria2url, data2)
    if req.status_code!=200:
        return
    else:
        status_dict = dict()
        results = req.json().get('result')
        results2 = req2.json().get('result')
        results.extend(results2)
        for res in results:
            status = res.get('status')
            completelen = int(res.get('completedLength'))
            totallen = int(res.get('totalLength'))
            filepath = res.get('files')[0].get('path').replace('//','/').replace("'","\\'")
            if completelen==totallen and completelen!=0:
                status = 'finished'
            status_dict[res.get('gid')] = {'status':status, 'completelen':completelen, 'filepath':filepath}
    return status_dict

# 功能：也是向Aria2发送另一种查询请求
def getdownloadings(status_dict):
    item = mq.fetchoneurl(mode='aria2')
    checkingidlist = list()
    while item:
        if item=='toomany':
            item = mq.fetchoneurl(mode='aria2')
            continue
        gid = item.get('oldpage')
        gid = gid or 'default'
        complete = status_dict.get(gid, {'status':'finished'})
        if complete.get('status')=='finished':
            mq.updateurl(item['id'])
            filepath = item['filepath']
            flag = unzipfile(filepath)
            removetask(taskid=gid)
        elif complete.get('completelen')==0 and complete.get('status')!='waiting':
            mq.reseturl(item['id'], 'checking', count=1)
            checkingidlist.append(item['id'])
        else:
            mq.reseturl(item['id'], 'checking')
            checkingidlist.append(item['id'])
        item = mq.fetchoneurl(mode='aria2')
    for id in checkingidlist:
        mq.reseturl(id, 'aria2')

# 功能：解压zip文件      
def unzipfile(filepath):
    kind = filetype.guess(filepath)
    if kind.extension!='zip':
        return None
    f = zipfile.ZipFile(filepath, 'r')
    flist = f.namelist()
    depstruct = [len(file.strip('/').split('/')) for file in flist]
    if depstruct[0]==1 and depstruct[1]!=1:
        try:
            f.extractall(path=os.path.dirname(filepath))
        except:
            return None
        else:
            return True
    else:
        try:
            f.extractall(path=os.path.splitext(filepath)[0])
        except:
            return None
        else:
            return True

#功能：把已完成的任务从队列里删除，以免后来的任务被阻塞
def removetask(taskid=None, address=None):
    id_str = "AriaNg_%s_0.043116476479668254"%str(int(time.time()))
    id = str(base64.b64encode(id_str.encode('utf-8')), 'utf-8')
    if taskid:
        data = json.dumps({"jsonrpc":"2.0","method":"aria2.forceRemove","id":id,"params":["token:%s"%aria2token,taskid]})
    if address:
        taskid = mq.fetchonegid(address)
        if taskid:
            data = json.dumps({"jsonrpc":"2.0","method":"aria2.forceRemove","id":id,"params":["token:%s"%aria2token,taskid]})
        else:
            data = json.dumps({"jsonrpc":"2.0","method":"aria2.forceRemove","id":id,"params":["token:%s"%aria2token,"default"]})
    req = requests.post(aria2url, data)
        
            
if __name__=="__main__":
    res = getinfos()
    if res:
        getdownloadings(res)