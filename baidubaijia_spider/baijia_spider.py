#!/usr/bin/env python
# -*- coding: utf-8 -*-



import json
# Third-Party Library

# My Library
from DFspider.spiders import WebSpider
from DFspider.instances import DownLoader, JsonSaver, CsvSaver, Parser, MysqlSaver
from DFspider.models import Request
from DFspider.util import get_logger


__author__ = "dong fang"
__created__ = "2017/1/7 21:26"

logger = get_logger()


class BaijiaParser(Parser):
    def parse(self, response):
        # response.encoding = "utf-8"
        json_dict = json.loads(response.text)
        artical_list = json_dict["data"]["list"]
        for artical in artical_list:
            artical_id = artical["ID"]
            artical_summary = artical["m_summary"]
            artical_tags = ",".join([tag["m_name"] for tag in artical["m_label_names"]])

            meta = {"artical_id": artical_id, "artical_summary": artical_summary, "content": artical_tags}
            artical_url = artical["m_display_url"]
            yield Request(url=artical_url, meta=meta, callback=self.parse_artical)

    def parse_artical(self, response):
        # response.encoding = "utf-8"
        title = response.xpath("//div[@id='page']/h1/text()")
        if title:
            artical_title = title[0]
        else:
            logger.error("无法获取文章标题,%s" % title)
            raise ValueError("无法获取文章的标题")
        artical_class = response.xpath("//div[@class='article-info'][2]/span/a/text()")
        if artical_class:
            artical_class = artical_class[0]
        else:
            logger.error("没有获取文章的类别")
        content = response.xpath("//div[@class='article-detail']/p[@class='text']/text()")
        if content:
            artical_content = "\n".join(content)
        else:
            logger.error("无法获取文章的内容")
            raise ValueError("无法获取文章的内容")
        artical_tags = response.meta["content"]
        artical_id = response.meta["artical_id"]
        artical_summary = response.meta["artical_summary"]

        artical = {
            "artical_id": artical_id,
            "artical_class": artical_class,
            "artical_title": artical_title,
            "artical_summary": artical_summary,
            "artical_content": artical_content,
            "artical_tags": artical_tags
        }
        print(artical)
        return {
            "artical_id": artical_id,
            "artical_class": artical_class,
            "artical_title": artical_title,
            "artical_summary": artical_summary,
            "artical_content": artical_content,
            "artical_tags": artical_tags
        }


def main():
    parser = BaijiaParser("cnbeta_spider")
    downloader = DownLoader(spider_name="baijia_spider", encoding="utf-8")
    saver = JsonSaver("baijia_spider")
    # saver = CsvSaver("cnbeta_spider", headers=["title", "introduction", "content"])
    # saver = MysqlSaver(spider_name="cnbeta_spider", user="root", pwd="123456", database="news")
    spider = WebSpider(spider_name="baijia_spider", downloader_cls=downloader, parser_cls=parser, saver_cls=saver)
    # lable_ids = ["100", "101", "102", "103", "104", "105", "106", "107", "108", "6", "3", "5", "4", "2", "8"]
    lable_ids = ["100"]
    start_urls = []
    for lable_id in lable_ids:
        for i in range(15):
            url = "http://baijia.baidu.com/ajax/labellatestarticle?page=%d&pagesize=20&labelid=%s&prevarticalid=746303" \
                  % (i, lable_id)
            start_urls.append(url)
    spider.start_request(start_urls)
    spider.start(downloader_num=5, parser_num=5, saver_num=5)


if __name__ == '__main__':
    main()
