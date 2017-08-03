#!/usr/bin/env python
# -*- coding: utf-8 -*-


import json

import pymongo

from ..util import db
from ..util.log import logger
from ..errors.errors import SaverError

__author__ = "dong fang"


class Saver(object):
    def __init__(self, spider_name):
        self.spider_name = spider_name

    def process_item(self, item, spider_name):
        """
        重写此方法  实现item的保存
        :param item:
        :param spider_name
        :return:
        """
        pass

    def save_item(self, item, spider_name):
        try:
            self.process_item(item, spider_name)
            return True
        except Exception as e:
            logger.error("%s, 保存失败\n" % item)
            logger.exception(e)
            raise SaverError("item保存失败")

    def close(self):
        pass


class JsonSaver(Saver):

    def __init__(self, spider_name):
        super(JsonSaver, self).__init__(spider_name)
        file_name = "%s.json" % self.spider_name
        self.fp = open(file_name, "w")

    def process_item(self, item, spider_name):
        json_str = json.dumps(item) + "\n"
        self.fp.write(json_str)
        self.fp.flush()

    def close(self):
        self.fp.close()


class CsvSaver(Saver):
    def __init__(self, spider_name, headers):
        Saver.__init__(self, spider_name)
        file_name = "%s.csv" % self.spider_name
        self.fp = open(file_name, "w")
        self.headers = headers
        header = ",".join(self.headers) + "\n"
        self.fp.write(header)

    def process_item(self, item, spider_name):
        """
        处理item，item是字典形式的数据，存储为csv文件（逗号分隔，各项中的英文逗号均替换为中文逗号）
        :param item:
        :param spider_name:
        :return:
        """
        row = ""
        for he in self.headers:
            row += item[he].replace(",", "，").encode("utf-8", "ignore")
        row += "\n"
        self.fp.write(row)
        self.fp.close()

    def close(self):
        self.fp.close()


class MysqlSaver(Saver):
    def __init__(self, spider_name, user, pwd, database, table=None, host="127.0.0.1", port=3306, charset="utf8"):
        super(MysqlSaver, self).__init__(spider_name=spider_name)
        db.create_engine(user, pwd, database, host, port, charset=charset)
        if table is None:
            logger.critical("数据库未设置表名，不能保存数据")
            raise SaverError("未数据库设置表名")
        else:
            self.table = table

    def process_item(self, item, spider_name):

        try:
            db.insert(self.table, **item)
            logger.info("item保存成功")
        except Exception as e:
            logger.error("item保存失败，%s" % item)
            logger.exception(e)
            raise SaverError("item保存失败")

    def close(self):
        pass


class MongodbSaver(Saver):
    def __init__(self, spider_name, database, collection, user=None, pwd=None, host="127.0.0.1", port=27017):
        super(MongodbSaver, self).__init__(spider_name)
        self.client = self._init_mongodb_conn(user, pwd, host, port)
        self.db = self.client[database]
        self.collection = self.db[collection]

    @staticmethod
    def _init_mongodb_conn(user, pwd, host, port):
        client = pymongo.MongoClient(host=host, port=port, username=user, password=pwd)
        return client

    def process_item(self, item, spider_name):
        pass

    def close(self):
        self.client.close()


if __name__ == '__main__':
    # conn = mysql.connector.connect(user="root", password="password")
    # cursor = conn.cursor()
    # print(cursor.execute("show databases"))
    # # print(cursor.fetchall())
    # dbs = [db[0] for db in cursor.fetchall()]
    # print(dbs)
    # cursor.execute("use juzi")
    # cursor.execute("show tables")
    # print(cursor.fetchall())
    # create_sql = "create table tset(?,?,?,?)"
    # print(create_sql.replace("?", ["qw", "er", "ty", "ui"]))
    list1 = [23, 34, 56, 67]
    list2 = [45, 67, 8, 9, 56]
    print(tuple(list1 + list2))
