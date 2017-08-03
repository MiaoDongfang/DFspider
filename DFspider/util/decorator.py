#!/usr/bin/env python
# -*- coding: utf-8 -*-


import functools
from datetime import datetime
import time

__author__ = "dong fang"


def time_recorder(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        start = datetime.now()
        print("程序开始运行,开始时间: %s" % start.strftime("%Y-%m-%d %H:%M:%S"))
        start_time = time.time()
        result = func(*args, **kwargs)
        print("程序开始运行,开始时间: %s" % start.strftime("%Y-%m-%d %H:%M:%S"))
        print("程序运行完成,完成时间: %s" % datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("程序运行共花费了 %f 秒" % (time.time()-start_time))
        return result

    return decorator
