#!/usr/bin/env python
# -*- coding: utf-8 -*-


from DFspider.instances import DownLoader

__author__ = "East"
__created__ = "2017/6/28 14:21"

if __name__ == '__main__':
    dl = DownLoader("test")
    resp = dl.get("http://www.baidu.com")
    print(dl.get_cookie().get_dict())
    print(resp.status_code)
