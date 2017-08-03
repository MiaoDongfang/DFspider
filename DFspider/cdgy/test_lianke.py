#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import threading
import requests
import time

__author__ = "dong fang"


class TestLianKe(threading.Thread):
    def run(self):
        print("正在请求")
        requests.get("http://www.liankewang.com/info/newsDetail?articleId=86537&website=")
        print("请求成功")


def main():
    start = time.time()
    liankes = [TestLianKe() for i in range(1000)]
    for thread in liankes:
        thread.setDaemon(True)
        thread.start()

    for thread in liankes:
        if thread.is_alive():
            thread.join()

    print("共耗时: %s" % str(time.time() - start))

if __name__ == '__main__':
    main()
