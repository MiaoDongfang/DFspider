#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import re
from lxml import html
from lxml import etree

if __name__ == '__main__':
    resp = requests.get("http://www.sccz.gov.cn/NewShow.jsp?action=1&id=3075&tname=%E5%85%AC%E5%91%8A%E5%85%AC%E7%A4%BA&TS=1490680337422")
    resp.encoding = "UTF-8"
    tree = html.fromstring(resp.text)
    content = tree.xpath("//table[@class='newtext02']")
    if content:
        appendixes = content[0].xpath("//td[@class='td_down']")
        if len(appendixes) > 0:
            for appendix in appendixes:
                # print(appendix[0].xpath("@onclick"))
                down_id = appendix.xpath("@onclick")[0][11:-1]
                root_url = "http://www.sccz.gov.cn/Site/DownAttach?id="
                url = root_url + down_id
                print(appendix.xpath("@onclick")[0][11:-1])
                print(appendix.xpath("text()"))
                # url = "http://www.sccz.gov.cn/Site/DownAttach?id=515"
                # a = etree.Element("a", href=url)
                link = etree.SubElement(appendix, "a")
                # link.text = appendix[0].xpath("text()")
                link.set("href", url)
                link.text = appendix.xpath("text()")[0]
                print(appendix.xpath("a/@href"))
                print(appendix.xpath("a/text()"))
                appendix.text = ""
            print(str(etree.tostring(content[0], encoding="utf-8"), encoding="utf-8"))
