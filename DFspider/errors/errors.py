#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "East"
__created__ = "2017/4/3 13:32"


class DownloaderError(Exception):
    def __init__(self, *args, **kwargs):
        super(DownloaderError, self).__init__(*args, **kwargs)
        self.exception = kwargs['exception'] if 'exception' in kwargs else None
        self.res = kwargs['res'] if 'res' in kwargs else None
        self.time_out = kwargs['time_out'] if 'time_out' in kwargs else False
        self.status_code = kwargs["status_code"] if 'status_code' in kwargs else None
        self.request = kwargs["request"] if "request" in kwargs else None
        self.url = kwargs["url"] if "url" in kwargs else None


class ParserError(Exception):

    def __init__(self, *args, **kwargs):
        super(ParserError, self).__init__(*args, **kwargs)
        self.url = kwargs["url"] if "url" in kwargs else None
        self.type = kwargs["type"] if "type" in kwargs else None


class OverTimeError(ParserError):
    """
    文章发布时间超过规定时间的异常
    """
    pass


class SaverError(Exception):
    pass
