#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "East"
__created__ = "2017/7/1 19:57"


class ProcessSaverException(object):
    def __init__(self, item, exception):
        self.item = item
        self.exception = exception
        self.saver_error_user_id_fp = open("saver_error_user_id.txt", "a", encoding="utf-8")
        self.saver_error_company_id_fp = open("saver_error_company_id.txt", "a", encoding="utf-8")

    def process(self):
        if "user_id" in self.item:
            self.saver_error_user_id_fp.write(self.item["user_id"] + "\n")
            self.saver_error_company_id_fp.flush()
        if "company_id" in self.item:
            self.saver_error_company_id_fp.write(self.item["company_id"] + "\n")
            self.saver_error_company_id_fp.flush()

    def close(self):
        self.saver_error_company_id_fp.close()
        self.saver_error_user_id_fp.close()
