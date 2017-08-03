#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..util.log import logger
from ..errors.errors import ParserError

__author__ = "dong fang"


class Parser(object):

    def __init__(self, spider_name):
        self.spider_name = spider_name

    def process_response(self, spider_name, response):
        pass

    def parse_item(self, response, spider_name, url_filter):
        try:
            logger.info("正在解析网页, %s, spider: %s" % (response.url, spider_name))
            callback_name = response.callback
            if callback_name is None:
                callback = self.parse
            else:
                if callable(callback_name):
                    callback = callback_name
                else:
                    callback = self.__getattribute__(callback_name)
            item = callback(response, url_filter)
            logger.info("网页解析成功, 正在返回数据: {item}".format(item=item))
            return item
        except Exception as e:
            logger.error("item解析失败\n%s" % str(e))
            raise ParserError("item解析失败")

    def parse(self, response, url_filter):
        return

    def close(self):
        pass
