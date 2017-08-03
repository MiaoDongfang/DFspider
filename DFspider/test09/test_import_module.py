#!/usr/bin/env python
# -*- coding: utf-8 -*-



__author__ = "dong fang"

if __name__ == '__main__':
    import importlib

    downloader_cls = "DFspider.instances.downloader.Downloader"
    Dowmloader = importlib.import_module(downloader_cls)
    dl = Dowmloader("test09")
    resp = dl.request("http://www.baidu.com")
    print(resp.text)
