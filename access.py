#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: access.py

Created on Mon Sep 23 20:18:01 2019

@author: qjfoidnh
"""

import os
import time

from init_process import DownEngine, fixexcepts
from logger_module import logger
from sql_module import mq

if __name__ == "__main__":
    engine = DownEngine()
    On = True
    print("%d进程开始运行..." % os.getpid())
    while On:

        # 先处理下载未完全的异常条目
        item = mq.fetchoneurl(mode="except")
        if type(item) == Exception:
            logger.error(item)
        elif not item:
            pass
        else:
            img_srcs = item['failed_links'];
            filepaths = item['failed_paths'];
            itemid = item['id'];
            raw_address = item['raw_address']

            res = fixexcepts(itemid, img_srcs, filepaths)
            if type(res) != int:
                logger.error(res)
                continue
            elif res == 0:
                logger.info("%d进程，%d号页面修复完毕.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
            elif res > 0:
                logger.warning("%d进程，%d号页面修复未完，仍余%d.\
                                页面地址为%s" % (os.getpid(), itemid, res, raw_address))

        item = mq.fetchoneurl()
        if item == 'toomany':  # 指取到的条目超过最大重试次数上限
            continue
        if type(item) == Exception:
            logger.error(item)
            continue
        elif not item:
            time.sleep(600)
            continue
        else:
            raw_address = item['raw_address'];
            itemid = item['id']
            logger.info("%d进程，%d号页面开始下载.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
            res = engine.engineEhentai(raw_address)
            if type(res) == Exception:
                logger.warning("%d进程，%d号页面引擎出错.\
                                出错信息为%s" % (os.getpid(), itemid, str(res)))
                mq.reseturl(itemid, 'skipped')
                continue

            if type(res) == tuple and len(res) == 2:
                response = mq.fixunfinish(itemid, res[0], res[1])
                if response == 0:
                    logger.warning("%d进程，%d号页面下载部分出错，已标志异常下载状态.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
                else:
                    logger.warning("%d进程，%d号页面下载部分出错且标志数据库状态字段时发生错误. 错误为%s, \
                                页面地址为%s" % (os.getpid(), itemid, str(response), raw_address))

            elif type(res) == dict:
                if 'taskid' in res:
                    response = mq.reseturl(itemid, 'aria2')
                    mq.replaceurl(itemid, res['taskid'], item['raw_address'], filepath=res['filepath'])

            elif res == 1:
                response = mq.updateurl(itemid)
                if type(response) == int:
                    logger.info("%d进程，%d号页面下载完毕.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
                else:
                    logger.warning("%d进程，%d号页面下载完毕但更新数据库状态字段时发生错误:%s.\
                                页面地址为%s" % (os.getpid(), itemid, str(response), raw_address))
            elif res == 2:
                response = mq.reseturl(itemid, 'pending', count=1)
                if type(response) == int:
                    logger.info("%d进程，%d号页面遭遇初始请求失败，已重置下载状态.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
                else:
                    logger.warning("%d进程，%d号页面遭遇初始请求失败，且重置数据库状态字段时发生错误.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
            elif res == 9:
                response = mq.reseturl(itemid, 'aria2')
                if type(response) == int:
                    logger.info("%d进程，%d号页面送入aria2下载器.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))
                else:
                    logger.warning("%d进程，%d号页面送入aria2下载器，但更新状态字段时发生错误.\
                                页面地址为%s" % (os.getpid(), itemid, raw_address))

            time.sleep(10)
