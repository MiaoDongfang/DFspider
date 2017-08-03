#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import random

from .util.config_util import CONFIG_USERAGENT_PC

__author__ = "dong fang"

configs = {
    "headers": {
        "User-Agent": random.choice(CONFIG_USERAGENT_PC)
    },
    "db": {
        "host": "112.74.45.98",
        "port": "3306",
        "user": "root",
        "password": ""
    },
    "download_sleep": 10,
    "url": {
        "url_pattern": "^((https|http|ftp|rtsp|mms)?://)[^\s]+",
        "black_url_list": [],
        "black_url_pattern_list": [],
        "white_url_pattern_list": ["^http"],
    },
    "file": {
        "appendix_downloaded_dir": "D:/appendixes"
    }
}

USER_AGENT = random.choice(CONFIG_USERAGENT_PC)

# database setting
HOST = "127.0.0.1"
PORT = "3306"
