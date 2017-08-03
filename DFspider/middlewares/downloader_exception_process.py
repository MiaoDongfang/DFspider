#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

# my Library
from ..util import db

__author__ = "dong fang"


class ProcessDownloaderExceptionBase(object):

    def __init__(self, request, exception):
        self.request = request
        self.exception = exception

    def process(self):
        pass

    def close(self):
        pass


class ProcessAppendixException(ProcessDownloaderExceptionBase):

    def process(self):
        unique_id = self.request.meta.get("unique_id")
        if unique_id is not None:
            db.update("update article set appendixFilePath=NULL WHERE uniqueId=?", unique_id)


class ProcessDownloaderError(ProcessDownloaderExceptionBase):
    def __init__(self, request, exception):
        super(ProcessDownloaderError, self).__init__(request, exception)
        self.downloader_error_fp = open("download_error_url.txt", "a", encoding="utf-8")

    def process(self):
        self.downloader_error_fp.write(self.request.url + "\n")
        pass

    def close(self):
        self.downloader_error_fp.close()

