#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

import requests

from DFspider.models import Response, Request

__author__ = "East"
__created__ = "2017/7/1 20:06"

if __name__ == '__main__':
    # fp = open("test.txt", "w", encoding="utf-8")
    # fp.write("asasasasa")
    # fp.flush()
    # time.sleep(20)
    # fp.close()

    company_intro1 = []
    company_intro2 = []
    company_intro3 = []
    company_intro4 = [""]
    print(any([company_intro1, company_intro2, company_intro3, company_intro4]))
    resp = requests.Response()
    resp.url = "http://www.baidu.com"
    res = Response(resp, Request())
    res.content = "asasasa"
    # res.url = "https://www.baidu.com"
    print(res.content)
    print(res.url)

    print("http" in "http://www")
