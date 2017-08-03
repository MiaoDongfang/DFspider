#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library


__author__ = "dong fang"


class DownloaderError(Exception):
    def __init__(self, **kwargs):
        self.exception = kwargs['exception'] if 'exception' in kwargs else None
        self.res = kwargs['res'] if 'res' in kwargs else None
        self.time_out = kwargs['time_out'] if 'time_out' in kwargs else False
        self.status_code = kwargs["status_code"] if 'status_code' in kwargs else None


if __name__ == '__main__':
    de = DownloaderError()
    de.exception = "123"
    de.status_code = 200
    print(de.status_code)
    print(de.exception)
