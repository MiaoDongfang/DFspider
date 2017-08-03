#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.util.log import logger
from DFspider.util import db

__author__ = "East"
__created__ = "2017/3/18 19:22"

if __name__ == "__main__":
    # 测试代码
    # for i in range(50):
    #     logger.error(i)
    #     logger.debug(i)
    # logger.critical("Database has gone away")
    print(db.next_id())
    print(db.next_id())
    print(len(db.next_id()))
