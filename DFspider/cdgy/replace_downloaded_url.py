#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import requests

__author__ = "dong fang"

resp = requests.get("http://www.cdht.gov.cn/attachment.jspx?cid=83831&i=0&t=1491664098424&k=0928127e7477eea559ce9b967c6f7e66")
print(resp.status_code)
with open("test.doc", "wb") as fp:
    fp.write(resp.content)
