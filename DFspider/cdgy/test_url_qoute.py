#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import urllib.parse

__author__ = "dong fang"

if __name__ == '__main__':
    url = urllib.parse.unquote(
        "http://www.sccz.gov.cn/NewShow.jsp?action=1&tname=%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA&TS=1490675830994&id=2799")
    print(url)
    url2 = urllib.parse.quote("http://www.sccz.gov.cn/NewShow.jsp?action=1&tname=公告公示&TS=1490675830994&id=2799",
                              safe=(58, 63, 38, 47, 61))
    url3 = "http://www.sccz.gov.cn/NewShow.jsp?action=1&tname=%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA&TS=1490675830994&id=2799"
    url4 = "http://www.sccz.gov.cn/NewShow.jsp?action=1&tname=%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA&TS=1490675830994&id=2799"
    print(url3 == url2)
    print(url4 == url2)
    print(url2)
