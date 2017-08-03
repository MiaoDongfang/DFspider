#!/usr/bin/env python
# -*- coding: utf-8 -*-



import json

from DFspider.instances import Saver

import sys
import imp

imp.reload(sys)
sys.setdefaultencoding("utf-8")

__author__ = "dong fang"


class DouBanBookSaver(Saver):

    def __init__(self, spider_name, book_file_path, comments_file_path):
        super(DouBanBookSaver, self).__init__(spider_name)
        self.book_fp = open(book_file_path, "a")
        self.comments_fp = open(comments_file_path, "a")

    def process_item(self, item, spider_name):
        if "book_name" in item:
            book_json = json.dumps(item)+"\n"
            self.book_fp.write(book_json)
        elif "comment_content" in item:
            comment_json = json.dumps(item)+"\n"
            self.comments_fp.write(comment_json)

    def close(self):
        super(DouBanBookSaver, self).close()
        self.book_fp.close()
        self.comments_fp.close()
