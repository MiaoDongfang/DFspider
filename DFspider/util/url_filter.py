#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

import re
import pybloom_live

from ..configs import configs
from . import db
from .log import logger
from .config_util import CONFIG_URLPATTERN_ALL

__author__ = "dong fang"

url_configs = configs.get("url")
BLACK_URL_LIST = url_configs.get("black_url_list", [])
BLACK_URL_PATTERN_LIST = url_configs.get("black_url_pattern_list", [])
WHITE_URL_PATTERN_LIST = url_configs.get("white_url_pattern_list", [])


class UrlFilter(object):
    """
    class of UrlFilter, to filter url by regexs and (bloomfilter or set)
    """

    def __init__(self, black_patterns=(CONFIG_URLPATTERN_ALL,), white_patterns=("^http",), capacity=None):
        """
        constructor, use variable of BloomFilter if capacity else variable of set
        """
        self.re_black_list = [re.compile(_pattern, flags=re.IGNORECASE) for _pattern in black_patterns]
        self.re_white_list = [re.compile(_pattern, flags=re.IGNORECASE) for _pattern in white_patterns]

        self.url_set = set() if not capacity else None
        self.bloom_filter = pybloom_live.ScalableBloomFilter(capacity, error_rate=0.001) if capacity else None
        return

    def update(self, url_list):
        """
        update this urlfilter using url_list
        """
        if self.url_set is not None:
            self.url_set.update(url_list)
        elif self.bloom_filter is not None:
            for url in url_list:
                self.bloom_filter.add(url)
        else:
            pass
        return

    def check(self, url):
        """
        check the url to make sure that the url hasn't been fetched
        """
        # regex filter: black pattern, if match one return False
        for re_black in self.re_black_list:
            if re_black.search(url):
                return False

        # regex filter: while pattern, if miss all return False
        result = False
        for re_white in self.re_white_list:
            if re_white.search(url):
                if self.url_set is not None:
                    result = (not (url in self.url_set))
                    self.url_set.add(url)
                elif self.bloom_filter is not None:
                    # "add": if key already exists, return True, else return False
                    result = (not self.bloom_filter.add(url))
                break

        return result


def _init_downloaded_urls_file(file_path):
    '''
    传入一个按行分割的downloaded urls 文件，每行代表一个url
    :param file_path:  文件地址
    :return: set  url集合
    '''
    fp = open(file_path, "r")
    urls = [url.replace("\n", "") for url in fp.readlines()]
    return list(set(urls))


def _init_downloaded_urls_db(table, url_field_name):
    try:
        results = db.select("select {url_field_name} from {table}".format(url_field_name=url_field_name, table=table))
        urls_list = [item[url_field_name] for item in results]
        return list(set(urls_list))
    except Exception as e:
        logger.exception(e)
        logger.fatal("从数据库中获得下载过的url失败,请检查程序")
        raise e


# 利用从配置文件中读取黑名单和白名单构建default url filter
default_url_filter = UrlFilter(black_patterns=BLACK_URL_PATTERN_LIST,
                               white_patterns=WHITE_URL_PATTERN_LIST)


def get_url_filter(data_type=None, table=None, url_field_name=None, file_path=None):
    url_filter = UrlFilter(black_patterns=BLACK_URL_PATTERN_LIST,
                           white_patterns=WHITE_URL_PATTERN_LIST)
    if data_type is None:
        pass
    elif data_type == "database":
        if isinstance(table, str) and isinstance(url_field_name, str):
            if table is not None and url_field_name is not None:
                try:
                    urls = _init_downloaded_urls_db(table, url_field_name)
                    url_filter.update(urls)
                except Exception:
                    pass
            else:
                pass
        if isinstance(table, (list, tuple)) and isinstance(url_field_name, (list, tuple)):
            if len(table) == len(url_field_name):
                for tb, field_name in zip(table, url_field_name):
                    try:
                        urls = _init_downloaded_urls_db(tb, field_name)
                        url_filter.update(urls)
                    except Exception:
                        pass
            else:
                raise ValueError("table数量和url_field_name数量必须相同")
        if isinstance(table, dict):
            for tb, field_name in table.items():
                try:
                    urls = _init_downloaded_urls_db(tb, field_name)
                    url_filter.update(urls)
                except Exception:
                    pass
    elif data_type == "file" and file_path is not None:
        try:
            urls = _init_downloaded_urls_file(file_path)
            url_filter.update(urls)
        except Exception:
            pass
    else:
        pass
    return url_filter
