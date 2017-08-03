#!/usr/bin/env python
# -*- coding: utf-8 -*-



from DFspider.instances import DownLoader
from DFspider.spiders import WebSpider
from DFspider.util import time_recorder
from .douban_parser import DouBanBookParser
from .douban_saver import DouBanBookSaver

__author__ = "dong fang"


@time_recorder
def main():
    parser = DouBanBookParser(spider_name="douban_book_spider")
    saver = DouBanBookSaver(spider_name="douban_book_spider", book_file_path="book.json",
                            comments_file_path="comments.json")
    downloader = DownLoader(spider_name="douban_book_spider", encoding="utf-8")
    spider = WebSpider(spider_name="douban_book_spider", downloader_cls=downloader, parser_cls=parser, saver_cls=saver)
    spider.start_request("https://book.douban.com/tag/?icn=index-nav")
    spider.start(downloader_num=2, parser_num=1, saver_num=1)

if __name__ == '__main__':
    main()
