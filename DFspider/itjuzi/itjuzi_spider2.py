#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from DFspider.spiders import WebSpider
from DFspider.instances import DownLoader, Parser, Saver
from DFspider.models import Request
from DFspider.util.log import logger
from DFspider.errors import ParserError

__author__ = "East"
__created__ = "2017/6/30 19:42"

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",

    "Host": "www.itjuzi.com",
}

USER_SAVE_IDS_FILE = "user_id_save.txt"
COMPANY_SAVE_IDS_FILE = "company_id_save.txt"

if os.path.exists(USER_SAVE_IDS_FILE):
    with open(USER_SAVE_IDS_FILE) as fp:
        lines = fp.readlines()
        USER_SAVE_IDS = set([line.strip() for line in lines])
else:
    USER_SAVE_IDS = set()

if os.path.exists(COMPANY_SAVE_IDS_FILE):
    with open(COMPANY_SAVE_IDS_FILE) as fp:
        lines = fp.readlines()
        for line in lines:
            line.strip()
        COMPANY_SAVE_IDS = set([line.strip() for line in lines])
else:
    COMPANY_SAVE_IDS = set()


class ItJuziParser(Parser):

    def parse(self, response, url_filter):
        html = response.content

        comment_num = response.xpath("//div[@class='tabset card-style']/a[4]/span/text()")
        if comment_num:
            comment_num = int(comment_num[0][1:-1])
        else:
            comment_num = None
        history_num = response.xpath("//div[@class='tabset card-style']/a[5]/span/text()")
        if history_num:
            history_num = int(history_num[0][1:-1])
        else:
            history_num = None
