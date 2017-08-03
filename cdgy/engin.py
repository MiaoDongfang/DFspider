#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.util import db

__author__ = "East"
__created__ = "2017/3/17 20:15"


def get_engine():
    db.create_engine(user="root", password="123456", database="pachong")