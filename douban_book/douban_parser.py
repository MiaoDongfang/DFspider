#!/usr/bin/env python
# -*- coding: utf-8 -*-


import urllib.parse

from DFspider.instances import Parser
from DFspider.models import Request
from DFspider.util import get_logger

import sys
import imp

imp.reload(sys)
sys.setdefaultencoding("utf-8")

__author__ = "dong fang"

logger = get_logger()


class DouBanBookParser(Parser):
    def __init__(self, spider_name):
        super(DouBanBookParser, self).__init__(spider_name)
        self.start_urls = "https://book.douban.com/tag/?icn=index-nav"
        self.root_url = "https://book.douban.com/"

    def parse(self, response):
        tag_trees = response.xpath("//div[@class='article']/div[2]/div")
        if tag_trees:
            for tag_tree in tag_trees:
                hrefs = tag_tree.xpath("table/tbody/tr/td/a/@href")
                second_book_classes = tag_tree.xpath("table/tbody/tr/td/a/text()")
                class_tag = tag_tree.xpath("a/h2/text()")
                first_book_class = "default"
                if class_tag:
                    first_book_class = class_tag[0].encode("utf-8").replace(b"\xc2\xb7", "").decode("utf-8")
                for href, second_book_class in zip(hrefs, second_book_classes):
                    url = urllib.parse.urljoin(self.root_url, href)
                    yield Request(url=url,
                                  meta={"first_book_class": first_book_class, "second_book_class": second_book_class},
                                  callback=self.parse_class_page, dont_filter=True)

    def parse_class_page(self, response):
        book_hrefs = response.xpath("//ul[@class='subject-list']/li/div[@class='info']/h2/a/@href")
        for book_href in book_hrefs:
            book_url = urllib.parse.urljoin(self.root_url, book_href)
            yield Request(book_url, meta=response.meta, callback=self.parse_book)
        next_page = response.xpath("//div[@class='paginator']/span[@class='next']/a/@href")
        if next_page:
            next_page_url = urllib.parse.urljoin(self.root_url, next_page[0])
            yield Request(url=next_page_url, meta=response.meta, callback=self.parse_class_page, dont_filter=True)

    def parse_book(self, response):
        book = {}
        book_id = response.url.split("/")[-2]
        book["book_id"] = book_id
        book_name = response.xpath("//div[@id='wrapper']/h1/span/text()")
        if book_name:
            book["book_name"] = book_name[0]
        else:
            raise KeyError("没有获得书名")
        rating = response.xpath("//div[@class='rating_self clearfix']/strong/text()")
        if rating:
            book["rating"] = rating[0]
        else:
            logger.error("没有获得评分数据")
        coment_peopele_count = response.xpath(
            "//div[@class='rating_right ']/div[@class='rating_sum']/span/a/span/text()")
        if coment_peopele_count:
            book["coment_peopele_count"] = coment_peopele_count[0]
        else:
            logger.error("没有获得评论人数")
        five_star = response.xpath("//span[@class='rating_per'][1]/text()")
        if five_star:
            book["five_star"] = five_star[0]
        else:
            logger.error("没有获得五星评分人数")
        four_star = response.xpath("//span[@class='rating_per'][2]/text()")
        if four_star:
            book["four_star"] = four_star[0]
        else:
            logger.error("没有获得四星评分人数")
        three_star = response.xpath("//span[@class='rating_per'][3]/text()")
        if three_star:
            book["three_star"] = three_star[0]
        else:
            logger.error("没有获得三星评分人数")
        two_star = response.xpath("//span[@class='rating_per'][4]/text()")
        if two_star:
            book["two_star"] = two_star[0]
        else:
            logger.error("没有获得两星评分人数")
        one_star = response.xpath("//span[@class='rating_per'][5]/text()")
        if one_star:
            book["one_star"] = one_star[0]
        else:
            logger.error("没有获得一星评分人数")

        datas = response.xpath("//div[@id='info']//text()")
        datas = [data.strip() for data in datas]
        datas = [data for data in datas if data != ""]

        book_author = ""
        book_press = ""
        book_year = ""
        book_pagenum = ""
        book_price = ""
        book_ISBN = ""

        for data in datas:
            if "作者" in data:
                if ":" in data:
                    book_author = datas[datas.index(data) + 1]
                elif ":" not in data:
                    book_author = datas[datas.index(data) + 2]
            # 找出版社中有个坑, 因为很多出版社名包含"出版社"
            # 如: 上海译文出版社，不能用下面注释的代码进行查找
            # elif u"出版社" in data:
            #    if u":" in data:
            #        item["press"] = datas[datas.index(data)+1]
            #    elif u":" not in data:
            #        item["press"] = datas[datas.index(data)+2]
            elif "出版社:" in data:
                book_press = datas[datas.index(data) + 1]
            elif "出版年:" in data:
                book_year = datas[datas.index(data) + 1]
            elif "页数:" in data:
                book_pagenum = datas[datas.index(data) + 1]
            elif "定价:" in data:
                book_price = datas[datas.index(data) + 1]
            elif "ISBN:" in data:
                book_ISBN = datas[datas.index(data) + 1]
        book["book_author"] = book_author
        book["book_press"] = book_press
        book["book_year"] = book_year
        book["book_pagenum"] = book_pagenum
        book["book_price"] = book_price
        book["book_ISBN"] = book_ISBN

        book_intro = response.xpath("//div[@id='link-report']//div[@class='intro']")
        if len(book_intro) == 1:
            book_desc = "\n".join(book_intro[0].xpath("p/text()"))
        elif len(book_intro) > 1:
            book_desc = "\n".join(book_intro[1].xpath("p/text()"))
        else:
            book_desc = ""
        book["book_desc"] = book_desc

        author_intro = response.xpath("//div[@class='indent ']//div[@class='intro']")

        if len(author_intro) == 1:
            author_desc = "\n".join(author_intro[0].xpath("p/text()"))
        elif len(author_intro) > 1:
            author_desc = "\n".join(author_intro[1].xpath("p/text()"))
        else:
            author_desc = ""

        book["author_desc"] = author_desc

        tags = "|".join(response.xpath("//div[@class='indent']/span/a[@class='tag']/text()"))
        book["tags"] = tags

        book["book_url"] = response.url
        book["first_book_class"] = response.meta["first_book_class"]
        book["second_book_class"] = response.meta["second_book_class"]

        yield book

        meta = response.meta
        meta["book_id"] = book_id

        short_comments_href = response.xpath("//div[@class='mod-hd']/h2/span[@class='pl']/a/@href")
        if short_comments_href:
            short_comments_url = urllib.parse.urljoin(self.root_url, short_comments_href[0])

            yield Request(short_comments_url, meta=meta, callback=self.parse_comments, dont_filter=True)
        else:
            logger.error("没有获取到评论页面链接")
        # reviews_href = response.xpath(
        #     "//section[@class='reviews mod book-content']/header/h2/span[@class='pl']/a/@href")
        # if reviews_href:
        #     reviews_url = urlparse.urljoin(self.root_url, reviews_href[0])
        #     yield Request(reviews_url, meta=meta, callback=self.parse_reviews)
        # else:
        #     logger.error(u"没有获得书评页面的链接")

    def parse_comments(self, response):
        comment = {}
        comments_items = response.xpath("//li[@class='comment-item']")
        for comments_item in comments_items:
            comment_content = comments_item.xpath("p[@class='comment-content']/text()")
            if comment_content:
                comment_content = comment_content[0]
                comment["comment_content"] = comment_content
            else:
                raise ValueError("未获得评论信息")
            comment_user = comments_item.xpath("h3/span[@class='comment-info']/a/text()")
            comment_user_url = comments_item.xpath("h3/span[@class='comment-info']/a/@href")
            if comment_user:
                comment_user = comment_user[0]
            else:
                comment_user = ""
                logger.error("comment user id 获取失败")
            comment["comment_user"] = comment_user
            if comment_user_url:
                comment_user_id = comment_user_url[0].split("/")[-2]
            else:
                comment_user_id = ""
                logger.error("comment user id 获取失败")
            comment["comment_user_id"] = comment_user_id
            rating = comments_item.xpath("h3/span[@class='comment-info']/span[1]/@title")
            if rating:
                rating = rating[0]
            else:
                rating = ""
                logger.error("rating 获取失败")
            comment["rating"] = rating
            comment_date = comments_item.xpath("h3/span[@class='comment-info']/span[2]/text()")
            if comment_date:
                comment_date = comment_date[0]
            else:
                comment_date = ""
                logger.error("comment_date 获取失败")
            comment["comment_date"] = comment_date
            comment_vote_num = comments_item.xpath("h3/span[@class='comment-vote']/span/text()")
            if comment_vote_num:
                comment_vote_num = comment_vote_num[0]
            else:
                comment_vote_num = ""
                logger.error("comment_vote_num 获取失败")
            comment["comment_vote_num"] = comment_vote_num

        yield comment

        next_page = response.xpath("//ul[@class='comment-paginator']/li[@class='p'][3]/a/@href")
        if next_page:
            next_page_url = urllib.parse.urljoin(self.root_url, next_page[0])
            yield Request(next_page_url, meta=response.meta, callback=self.parse_comments, dont_filter=True)
