#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.instances import DownloaderError
from DFspider.instances import DownLoader
from DFspider.models import Request
from DFspider.errors import ParserError

__author__ = "East"
__created__ = "2017/4/3 20:11"

if __name__ == '__main__':
    dl = DownLoader("test09")
    # resp = dl.download(Request(url="https://www.baidu.com"))
    # resp = dl.download(Request(url="https://www.baidu.com"))
    # resp = dl.download(Request(url="https://www.baidu.com"))
    # resp = dl.download(Request(url="https://www.baidu.com"))
    # resp = dl.download(Request(url="https://www.baidu.com"))
    # resp = dl.download(Request(url="https://www.baidu.com"))
    # print(Request(url="http://www.baidu.com").request_dict)
    # title = resp.xpath("//form[@id='form']/span/input[@id='su']/@value")[0]
    # print(resp.xpath("//form[@id='form']/span/input[@id='su']/@value")[0])
    # print(title)

    # try:
    #     resp = dl.download(
    #         Request(url="http://www.cdst.gov.cn:801/", retry_times=0))
    # # resp = requests.get("http://www.cdst.gov.cn/Type.asp?typeid=47&BigClassid=181&page=1")
    # except DownloaderError as e:
    #     print(e.status_code)
    #     print(e.exception)
    #     print(type(e))

    resp = dl.download(
            Request(url="http://www.cdst.gov.cn:801/", retry_times=0))

    import requests
    from requests import exceptions
    try:
        resp = requests.get("http://www.cdst.gov.cn:801/")
    except exceptions as e:
        print(e)

    # pe = ParserError(type="list", url="121212",)
    # print(pe)
