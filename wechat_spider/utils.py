#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

from DFspider.util import db

__author__ = "dong fang"


def is_in_db(value, table, field):
    item = db.select("select * from "+table+" WHERE "+field+"=?", value)
    return bool(item)


if __name__ == '__main__':
    db.create_engine(user="root", password="123456", database="pachong")
    print(is_in_db("asas", "post", "content_url"))
