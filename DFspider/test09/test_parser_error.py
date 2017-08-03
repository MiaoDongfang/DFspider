#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

from DFspider.middlewares.parser_exception_process import ProcessParserException
from DFspider.instances import ParserError

__author__ = "dong fang"

error = ParserError("123")
error.url = "http://www.baidu.com"
print(error.type)
print(error.url)
print(str(error))
