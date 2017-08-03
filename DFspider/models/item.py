#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from ..util import db
from ..util.db import DBError
from ..configs import configs
from ..util.log import logger

__author__ = "East"
__created__ = "2017/3/17 20:22"


class Item(dict):
    def __init__(self, **kwargs):
        super(Item, self).__init__(**kwargs)
        db_configs = configs.get("db", None)
        if db_configs is None:
            logger.critical("没有配置数据库连接信息，不能保存数据")
            raise DBError("未找到数据库连接信息")
        else:
            user = db_configs.get("user", "root")
            pwd = db_configs.get("password", "123456")
            host = db_configs.get("host", "127.0.0.1")
            port = db_configs.get("port", 3306)
            database = db_configs.get("database", "None")

            if database is None:
                logger.critical("未配置数据库名，不能保存数据")
                raise DBError("未配置数据库名")

            db.create_engine(user, pwd, database, host, port)

    def to_json(self):
        return json.dumps(self)

    def insert_to_db(self, table):
        db.insert(table, **self)


class ItemDao(object):
    def __init__(self):
        db_configs = configs.get("db", None)
        if db_configs is None:
            logger.critical("没有配置数据库连接信息，不能保存数据")
            raise DBError("未找到数据库连接信息")
        else:
            user = db_configs.get("user", "root")
            pwd = db_configs.get("password", "123456")
            host = db_configs.get("host", "127.0.0.1")
            port = db_configs.get("port", 3306)
            database = db_configs.get("database", "None")

            if database is None:
                logger.critical("未配置数据库名，不能保存数据")
                raise DBError("未配置数据库名")

            db.create_engine(user, pwd, database, host, port)

    @staticmethod
    def insert(table, item):
        db.insert(table, **item)

if __name__ == '__main__':
    pass
