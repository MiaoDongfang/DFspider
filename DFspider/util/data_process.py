#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import uuid
from datetime import datetime, date

__author__ = "dong fang"
__all__ = ["next_id", "differ_month"]


def next_id(t=None):
    """
    用于构造下一个id
    :param t:
    :return:
    """
    if t is None:
        t = time.time()
    return "%015d%s000" % (int(t * 1000), uuid.uuid4().hex)


def differ_month(date1, date2, date_format="%Y-%m-%d"):
    """
    计算两个日期之间相差的月份, date2-date1
    :param date1:
    :param date2:
    :param date_format
    :return:
    """
    if isinstance(date1, str) and isinstance(date2, str):
        date1 = datetime.strptime(date1, date_format)
        date2 = datetime.strptime(date2, date_format)
    elif isinstance(date1, (datetime, date)) and isinstance(date2, (datetime, date)):
        pass
    elif isinstance(date1, (datetime, date)) and isinstance(date2, str):
        date2 = datetime.strptime(date2, date_format)
    elif isinstance(date1, str) and isinstance(date2, (date, datetime)):
        date1 = datetime.strptime(date1, date_format)
    else:
        raise ValueError("the date must be date, datetime or string")
    return -((date1.year-date2.year)*12+(date1.month-date2.month))


if __name__ == "__main__":
    print(next_id())
    print(len(next_id()))
    print(next_id())
    print(len(next_id()))
    print(differ_month("2014-11-1", "2015-12-1"))
    print(differ_month("2015-10-8", "2014-11-1"))
    print(differ_month("2015-10", "2015-9", "%Y-%m"))
    print(datetime.strptime("2014-11-1", "%Y-%m-%d"))
