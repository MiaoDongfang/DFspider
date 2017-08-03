#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.instances import DownLoader
from DFspider.models import Request

__author__ = "East"
__created__ = "2017/3/17 18:51"

if __name__ == '__main__':
    dl = DownLoader("test")
    resp = dl.download(Request(url="http://sheyu.baijia.baidu.com/article/796060"))
    print((resp.text))
    print((resp.xpath("//div[@id='page']/h1/text()")[0]))
