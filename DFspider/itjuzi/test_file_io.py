#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.errors import ParserError
from DFspider.middlewares.downloader_exception_process import ProcessDownloaderError

__author__ = "East"
__created__ = "2017/7/1 18:05"


def test_exception():
    raise ParserError("this is a test for ParserError")


class TestClass(object):

    def process(self):
        self.pde = 10

    def print_test(self):
        print(self.pde)


if __name__ == '__main__':
    # fp = open("user_id_save.txt", "a", encoding="utf-8")
    # for i in range(10):
    #     fp.write(str(i) + "\n")
    #
    # fp.close()

    # with open("user_id_save.txt", "a", encoding="utf-8") as fp2:
    #     fp2.write("110\n")

    # with open("user_id_save.txt", "r", encoding="utf-8") as fp3:
    #     lines = fp3.readlines()
    #     print(type(lines))
    #     print(list(lines))
    #     lines = [line.strip() for line in lines]
    #     for line in lines:
    #         line.strip()
    #     print(lines)
    #     user_id_set = set(lines)
    # print(user_id_set)
    # print(str(1) in user_id_set)

    url = "https://www.itjuzi.com/user/360983"
    url2 = "https://www.itjuzi.com/user/360983?page=2"
    print(url.split("?")[0])
    print(url2.split("?")[0])

    try:
        test_exception()
    except ParserError as e:
        print(str(e))

    tc = TestClass()
    tc.process()
    tc.print_test()
    # print(tc.pde)
