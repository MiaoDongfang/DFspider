#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import db

__author__ = "East"
__created__ = "2017/3/17 20:15"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = "3306"


def get_engine():
    db.create_engine(user="root", password="123456", database="pachong")
