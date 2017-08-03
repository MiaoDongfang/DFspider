#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import requests
import re
from lxml import html
from lxml import etree
import json
import urllib

__author__ = "dong fang"

if __name__ == '__main__':
    url1 = "http://www.cdht.gov.cn/zwgktzgg/65464.jhtml"
    url2 = "http://www.cdht.gov.cn/zwgktzgg/71451.jhtml"
    cid = re.search("\d+", url1).group()
    # base_url = "http://www.cdht.gov.cn/attachment_url.jspx?cid=71451&n=1"
    base_url = "http://www.cdht.gov.cn/attachment_url.jspx?cid="
    appendix_base_url = "http://www.cdht.gov.cn/attachment.jspx?cid=" + cid + "&i="
    resp = requests.get(url1)
    tree = html.fromstring(resp.text)
    content = tree.xpath("//div[@class='xw_xxym']")
    appendixes = content[0].xpath("div[3]/a")
    if len(appendixes) > 0:
        n = len(appendixes)
        req_url = base_url + cid + "&n=" + str(n)
        json_resp = requests.get(req_url)
        # print(json.loads(json_resp.text)[0])
        download_list = json.loads(json_resp.text)
        for i in range(len(appendixes)):
            print(download_list[i])
            appendix_url = appendix_base_url + str(i) + download_list[i]
            appendixes[i].set("href", appendix_url)
            print(appendixes[i].xpath("@href"))
            print(appendix_url.encode("utf-8"))
        # for index, appendix, download_str in zip(appendixes, download_list):
        #     print(index)
        #     print(appendix)
        #     print(download_str)
    content = etree.tostring(content[0], encoding="utf-8")
    content = str(content, encoding="utf-8")
    print(content.replace("amp;", ""))
