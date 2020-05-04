#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filename: sql_module.py

Created on Sun Sep 22 23:24:39 2019

@author: qjfoidnh
"""

import pymysql
from pymysql.err import IntegrityError


class MySQLconn_url(object):
    def __init__(self):

        self.conn = pymysql.connect(
            host='127.0.0.1',
            port=3307,
            user='root',
            password='bingo',
            database='comics_local',
        )
        self.conn.autocommit(True)  # 开启自动提交，生产环境不建议数据库DBA这样做
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)
        # 让MySQL以字典形式返回数据

    def __del__(self):

        self.conn.close()

    # 功能：取指定状态的一条数据
    def fetchoneurl(self, mode="pending", tabname='comic_urls'):

        sql = "SELECT * FROM %s \
                WHERE status = '%s'" % (tabname, mode)
        self.conn.ping(True)  # mysql长连接防止timeut自动断开
        try:
            self.cursor.execute(sql)
        except Exception as e:
            return e
        else:
            item = self.cursor.fetchone()
            if not item:
                return None
            if mode == "pending" or mode == 'aria2':
                if item['checktimes'] < 3:
                    sql = "UPDATE %s SET starttime = now(), status = 'ongoing' WHERE id = %d" % (tabname, item['id'])
                    #print()
                else:
                    sql = "UPDATE %s SET status = 'error' \
                    WHERE id = %d" % (tabname, item['id'])
                    if mode == 'aria2':
                        sql = "UPDATE %s SET status = 'pending', checktimes = 0, raw_address=CONCAT('chmode',raw_address) \
                    WHERE id = %d" % (tabname, item['id'])
                    self.cursor.execute(sql)
                    return 'toomany'
            elif mode == "except":
                sql = "UPDATE %s SET status = 'ongoing' \
                WHERE id = %d" % (tabname, item['id'])
            try:
                self.cursor.execute(sql)
            except Exception as e:
                self.conn.rollback()
                return e
            else:
                return item

    # 功能：更新指定id条目的状态字段
    def updateurl(self, itemid, status='finished', tabname='comic_urls'):
        sql = "UPDATE %s SET endtime = now(),status = '%s' WHERE id = %d" % (tabname, status, itemid)
        self.conn.ping(True)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            self.conn.rollback()
            return e
        else:
            return itemid

    # 功能：更新指定id条目状态及重试次数字段
    def reseturl(self, itemid, mode, count=0, tabname='comic_urls'):

        sql = "UPDATE %s SET status = '%s', checktimes=checktimes+%d WHERE id = %d" % (tabname, mode, count, itemid)
        self.conn.ping(True)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            print(e)
            self.conn.rollback()
            return e
        else:
            return itemid

    # 功能：将未下载完成图片的网址列表写入数据库，
    def fixunfinish(self, itemid, img_urls, filepaths, tabname='comic_urls'):

        img_urls = "Š".join(img_urls)  # 用不常见拉丁字母做分隔符，避免真实地址中有分隔符导致错误分割
        filepaths = "Š".join(filepaths)
        sql = "UPDATE %s SET failed_links = '%s', failed_paths = '%s', status='except' WHERE id = %d" % (
            tabname, img_urls, filepaths, itemid)
        self.conn.ping(True)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            self.conn.rollback()
            return e
        else:
            return 0

    # 功能：在尝试完一次未完成补全后，更新未完成列表
    def resetunfinish(self, itemid, img_urls, filepaths, tabname='comic_urls'):
        failed_num = len(img_urls)
        if failed_num == 0:
            sql = "UPDATE %s SET failed_links = null, failed_paths = null, status = 'finished', endtime = now() WHERE id = %d" % (
                tabname, itemid)
        else:
            img_urls = "Š".join(img_urls)  # 用拉丁字母做分隔符，避免真实地址中有分隔符导致错误分割
            filepaths = "Š".join(filepaths)
            sql = "UPDATE %s SET failed_links = '%s', failed_paths = '%s', status = 'except' WHERE id = %d" % (
                tabname, img_urls, filepaths, itemid)
        self.conn.ping(True)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            self.conn.rollback()
            return e
        else:
            return failed_num

    # 功能：为条目补上资源名称
    def addcomicname(self, address, title, tabname='comic_urls'):
        sql = "UPDATE %s SET comic_name = '%s' WHERE raw_address = '%s'" % (
            tabname, title, address)  # 由于调用地点处没有id值，所以这里用address定位。也是本项目中唯二处用address定位的
        self.conn.ping(True)
        try:
            self.cursor.execute(sql)
        except IntegrityError:
            self.conn.rollback()
            sql_sk = "UPDATE %s SET status = 'skipped' \
                    WHERE raw_address = '%s'" % (tabname, address)
            self.cursor.execute(sql_sk)
            return Exception(title + " Already downloaded!")
        except Exception as e:
            self.conn.rollback()
            return e
        else:
            return 0

    # 功能：通过网址查询标识Aria2里对应的gid
    def fetchonegid(self, address, tabname='comic_urls'):
        sql = "SELECT * FROM %s \
                WHERE raw_address = '%s'" % (tabname, address)
        self.conn.ping(True)
        try:
            self.cursor.execute(sql)
        except Exception as e:
            return e
        else:
            item = self.cursor.fetchone()
            if not item:
                return None
            else:
                return item.get('oldpage')


mq = MySQLconn_url()
