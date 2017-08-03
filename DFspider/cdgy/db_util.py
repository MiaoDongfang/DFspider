#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.util import db
from DFspider.util.engine import get_engine

__author__ = "East"
__created__ = "2017/3/19 0:24"

if __name__ == '__main__':
    get_engine()
    with open("downloaded.txt","r") as fp:
        lines = fp.readlines()
        for line in lines:
            url = line.replace("\n", "").strip()
            db.insert("downloaded_url", url=url)
    print("处理完成")

