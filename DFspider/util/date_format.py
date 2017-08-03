#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import re

DATE_REGEX_FORMAT_DICT = {
    r"^\d{4}-\d{1,2}-\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}$": "%Y-%m-%d %H:%M:%S",
    r"^\d{4}-\d{1,2}-\d{1,2}$": "%Y-%m-%d",
    r"^\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}$": "%Y/%m/%d %H:%M:%S",
    r"^\d{4}/\d{1,2}/\d{1,2}$": "%Y/%m/%d",
    r"^\d{4}\\\d{1,2}\\\d{1,2}\s+\d{1,2}:\d{1,2}:\d{1,2}$": "%Y\\%m\\%d %H:%M:%S",
    r"^\d{4}\\\d{1,2}\\\d{1,2}$": "%Y\\%m\\%d",
    r"^\d{4}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{1,2}:\d{1,2}$": "%Y年%m月%d日 %H:%M:%S",
    r"^\d{4}年\d{1,2}月\d{1,2}日$": "%Y年%m月%d日",
}


def date_format(date_str: str, format_str=None):
    if format_str is None:
        date_str = date_str.replace("：", ":")
        for item in DATE_REGEX_FORMAT_DICT.items():
            # print(item)
            date_pattern = re.compile(item[0])
            if date_pattern.match(date_str):
                return datetime.strptime(date_str, item[1])
    else:
        datetime.strptime(date_str, format_str)

if __name__ == '__main__':
    print(date_format("2016-01-01 00:00:00"))
