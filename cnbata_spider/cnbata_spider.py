#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library


import json
import urllib.parse
# Third-Party Library

# My Library
from DFspider.util import time_recorder
from DFspider.spiders import WebSpider
from DFspider.instances import DownLoader, JsonSaver, CsvSaver, Parser, MysqlSaver
from DFspider.models import Request

__author__ = "dong fang"


class CnBetaParser(Parser):

    def parse(self, response):
        hrefs = response.xpath("//div[@id='hot']/dl/dt/a/@href")
        # hrefs += response.xpath("//div[@class='hd']/div[@class='title']/a/@href")
        for href in hrefs:
            url = urllib.parse.urljoin("http://www.cnbeta.com/", href)
            yield Request(url=url, callback=self.parse_artical)

    def parse_artical(self, response):
        title = response.xpath("//h2[@id='news_title']/text()")
        title = "".join(title)
        introduction = response.xpath("//div[@class='introduction']/p/text()")
        introduction = "".join(introduction)
        content = response.xpath("//section[@class='article_content']/div[@class='content']/*/text()")
        content = "".join(content)

        yield {"title": title, "introduction": introduction, "content": content}


# from spider import BaseSpider
#
#
# class CnBeatSpider02(BaseSpider):
#
#     start_urls = "http://www.cnbeta.com"
#     downloader = DownLoader(spider_name="cnbeta")
#
#     def __init__(self):
#         BaseSpider.__init__(self, "http://www.cnbeta.com")
#         self.fp = open("artical.json", "w")
#
#     def parse(self, response):
#         # response = self.downloader.download(Request(self.start_urls))
#         hrefs = response.xpath("//div[@id='hot']/dl/dt/a/@href")
#         hrefs += response.xpath("//div[@class='hd']/div[@class='title']/a/@href")
#         for href in hrefs:
#             url = urlparse.urljoin("http://www.cnbeta.com/", href)
#             self.download_url(url=url, callback=self.parse_artical)
#
#     def parse_artical(self, response):
#         title = response.xpath("//h2[@id='news_title']/text()")
#         introduction = response.xpath("//div[@class='introduction']/p/text()")
#         content = response.xpath("//section[@class='article_content']/div[@class='content']/text()")
#
#         artical = {"title": title, "introduction": introduction, "content": content}
#         self.item_save(artical)
#
#     def item_save(self, item):
#         json_str = json.dumps(item)
#         self.fp.write(json_str)
#
#     def close(self):
#         self.fp.close()


@time_recorder
def main():
    parser = CnBetaParser("cnbeta_spider")
    downloader = DownLoader(spider_name="cnbeta_spider")
    saver = JsonSaver("cnbeta_spider")
    spider = WebSpider(spider_name="cnbeta_spider", downloader_cls=downloader, parser_cls=parser, saver_cls=saver)
    spider.start_request("http://www.cnbeta.com/")
    spider.start()


@time_recorder
def main03():
    parser = CnBetaParser("cnbeta_spider")
    downloader = DownLoader(spider_name="cnbeta_spider", encoding="utf-8")
    saver = JsonSaver("cnbeta_spider")
    # saver = CsvSaver("cnbeta_spider", headers=["title", "introduction", "content"])
    # saver = MysqlSaver(spider_name="cnbeta_spider", user="root", pwd="password", database="cnbeta")
    spider = WebSpider(spider_name="cnbeta_spider", downloader_cls=downloader, parser_cls=parser, saver_cls=saver)
    spider.start_request("http://www.cnbeta.com/")
    spider.start(downloader_num=3, parser_num=1, saver_num=1)


# @time_recorder
# def main02():
#     spider = CnBeatSpider02()
#     spider.download_start_url()
#     spider.close()


if __name__ == '__main__':
    main03()
