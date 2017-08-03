#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
from datetime import datetime

from ..instances.parser import ParserError
from ..util import db

__author__ = "dong fang"


class ProcessParserException(object):
    def __init__(self, response, exception):
        self.response = response
        self.exception = exception
        self.parser_error_url_fp = open("parser_error_url.txt", "a", encoding="utf-8")

    def process(self):
        self.parser_error_url_fp.write(self.response.url + "\n")

    def close(self):
        self.parser_error_url_fp.close()
