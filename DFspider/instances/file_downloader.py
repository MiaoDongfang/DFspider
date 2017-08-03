#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .downloader import DownLoader

__author__ = "East"
__created__ = "2017/3/19 17:57"


class FileDownloader(DownLoader):
    def __init__(self, **kwargs):
        super(FileDownloader, self).__init__(self, kwargs)

