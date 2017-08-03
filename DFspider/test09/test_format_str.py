#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "East"
__created__ = "2017/3/18 21:39"

if __name__ == '__main__':
    next_page_get_url = 'http://www.cdgy.gov.cn/newList1Level.jsp?classId=010501&p={page}'
    next_page = 2
    next_page_get_url = next_page_get_url.format(page=next_page)
    print(next_page_get_url)
