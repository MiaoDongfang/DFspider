#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import re
import json
import os

# Third-Party Library

# My Library
from DFspider.spiders import WebSpider
from DFspider.instances import DownLoader, Parser, Saver, MysqlSaver
from DFspider.models import Request
from DFspider.util.log import logger
from DFspider.errors import ParserError
from DFspider.util import db
from mysql.connector.errors import IntegrityError

__author__ = "East"
__created__ = "2017/6/30 19:42"

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding":"gzip, deflate, br",
    "Host": "www.itjuzi.com",
}

USER_SAVE_IDS_FILE = "user_id_save.txt"
COMPANY_SAVE_IDS_FILE = "company_id_save.txt"

if os.path.exists(USER_SAVE_IDS_FILE):
    with open(USER_SAVE_IDS_FILE) as fp:
        lines = fp.readlines()
        USER_SAVE_IDS = set([line.strip() for line in lines])
else:
    USER_SAVE_IDS = set()

if os.path.exists(COMPANY_SAVE_IDS_FILE):
    with open(COMPANY_SAVE_IDS_FILE) as fp:
        lines = fp.readlines()
        for line in lines:
            line.strip()
        COMPANY_SAVE_IDS = set([line.strip() for line in lines])
else:
    COMPANY_SAVE_IDS = set()


class ItJuziParser(Parser):
    def parse(self, response, url_filter):
        # user_id = response.url.split("/")[-1]
        result = db.select_one("select * from `user` WHERE user_id=?", response.meta["user_id"])
        if result:
            raise ParserError("该user已经抓取，user_id: %s" % response.meta["user_id"])
        # if str(response.meta["user_id"]) in USER_SAVE_IDS:
        #     raise ParserError("该user已经抓取，user_id: %s" % response.meta["user_id"])

        html = {
            "url": response.url,
            "html": response.text,
            "type": "user",
            "obj_id": str(response.meta["user_id"]),
            "page": response.meta["follow_page"]
        }
        if not db.select_one("select * from html WHERE url LIKE ?", "%" + response.url[5:]):
            yield html

        if "user_follow_company_ids" in response.meta:
            user_follow_company_ids = response.meta["user_follow_company_ids"]
        else:
            user_follow_company_ids = []
        company_urls = response.xpath("//ul[@class='list-commen-withpic with-min-height']/"
                                      "li/div[@class='picinfo']/div[@class='right']/sapn[@class='titel']/a/@href")
        if company_urls:
            for company_url in company_urls:
                # https://www.itjuzi.com/company/61394
                yield Request(url=str(company_url), callback=self.parse_company_info)
                try:
                    company_id = re.fullmatch("https*://www.itjuzi.com/company/(\d+)", company_url).group(1)
                    company_id = int(company_id)
                    # company_ids.append(company_id)
                    user_follow_company_ids.append(company_id)
                except AttributeError:
                    logger.error("无法是用正则表达式从company_url中提取到company_id, company_url: %s" % company_url)
                pass
        if len(company_urls) == 10:
            if response.meta.get("follow_page_num", None) is not None:
                follow_page_num = response.meta["follow_page_num"]
            else:
                count = response.xpath(
                    "//div[@class='titlebar bg-gray']/div[@class='tabset card-style']/a[@class='tab on']/span/text()")
                if count:
                    count = int(count[0][1:-1])
                    follow_page_num = count / 10 + 1
                else:
                    follow_page_num = None
                    logger.error("无法提取用户行为数据的总数")
            if follow_page_num is not None:
                if response.meta["follow_page"] < follow_page_num:
                    next_page = response.meta["follow_page"] + 1
                    next_page_url = response.url.split("?")[0] + "?page=%d" % next_page
                    response.meta["user_follow_company_ids"] = user_follow_company_ids
                    response.meta["follow_page"] = next_page
                    response.meta["follow_page_num"] = follow_page_num
                    yield Request(url=next_page_url, meta=response.meta, callback=self.parse)
                    # if page <= page_num:
                    #     parse_user_active(user_id, active_type, page)
        response.meta["user_follow_company_ids"] = user_follow_company_ids

        # 抓取用户的基本信息
        user_area = response.xpath("//div[@class='pad base-info']/p[1]/text()")
        if user_area:
            user_area = user_area[0]
        else:
            logger.info("无法提取user_area 可能是没有相关信息或提取失败")
            user_area = ""
        user_intro = response.xpath("//div[@class='pad base-info']/p[2]/text()")
        if user_intro:
            user_intro = user_intro[0]
        else:
            logger.info("无法提取user_intro 可能是没有相关信息或提取失败")
            user_intro = ""
        user_gz_field = response.xpath("//div[@class='pad tagset']/span[@class='tag']/text()")
        if user_gz_field:
            user_gz_field = "|".join(user_gz_field)
        else:
            logger.info("无法提取user_gz_field 可能是没有填写或者提取失败")
            user_gz_field = ""
        user_for = response.xpath("//div[@class='pad']/ul[@class='list-smallgray']/li/text()")
        if user_for:
            user_for = "|".join(user_for)
        else:
            logger.info("无法提取user_for 可能是没有相关信息或提取失败")
            user_for = ""

        user_info = {
            "user_id": response.meta["user_id"],
            "user_area": str(user_area),
            "user_intro": str(user_intro),
            "user_gz_field": str(user_gz_field),
            "user_for": str(user_for),
        }

        response.meta["user_info"] = user_info
        next_url = "https://www.itjuzi.com/user/get_follow_history/%s" % response.meta["user_id"]
        response.meta["history_page"] = 1
        yield Request(url=next_url, callback=self.parse_user_history, meta=response.meta)

        # comment_num = response.xpath("//div[@class='tabset card-style']/a[4]/span/text()")
        # if comment_num:
        #     comment_num = int(comment_num[0][1:-1])
        # else:
        #     comment_num = None
        # history_num = response.xpath("//div[@class='tabset card-style']/a[5]/span/text()")
        # if history_num:
        #     history_num = int(history_num[0][1:-1])
        # else:
        #     history_num = None
        #
        # response.meta["user_info"] = user_info
        # if history_num > 0 and history_num is not None:
        #     next_url = "https://www.itjuzi.com/user/get_follow_history/%s" % response.meta["user_id"]
        #     response.meta["history_page"] = 1
        #     yield Request(url=next_url, callback=self.parse_user_history, meta=response.meta)
        # elif comment_num > 0 and comment_num is not None:
        #     next_url = "https://www.itjuzi.com/user/get_follow_history/%s" % response.meta["user_info"]["user_id"]
        #     response.meta["user_history_company_ids"] = []
        #     response.meta["comment_page"] = 1
        #     yield Request(url=next_url, callback=self.parse_comment_company, meta=response.meta)
        # else:
        #     user_comment_company_ids = ""
        #     user_history_company_ids = ""
        #     user_info["user_history_company_ids"] = user_history_company_ids
        #     user_info["user_comment_company_ids"] = user_comment_company_ids
        #     yield user_info
            # url = "https://www.itjuzi.com/user/get_follow_company/%s" % user_id
            # yield Request(url=url, callback=self.parse_user_follow, meta={"user_info": user_info, "follow_page": 1})

    def parse_company_info(self, response, url_filter):
        company_id = response.url.split("/")[-1]
        result = db.select_one("select company_id from company WHERE company_id=?", company_id)
        if result:
            raise ParserError("该company已经抓取, company_id: %s" % company_id)
        # if company_id in COMPANY_SAVE_IDS:
        #     raise ParserError("该company已经抓取, company_id: %s" % company_id)

        html = {
            "url": response.url,
            "html": response.text,
            "type": "company",
            "obj_id": str(company_id),
        }
        if not db.select_one("select * from html WHERE url LIKE ?", "%" + response.url[5:]):
            yield html
        # yield html

        company_name = response.xpath("//h1[@class='seo-important-title']/text()")
        if company_name:
            company_name = company_name[0]
            company_name = company_name.replace("\n", "").replace("\t", "")
        else:
            logger.error("提取company_name失败, company_id: %s" % company_id)
            company_name = ""
        company_scope = response.xpath("//span[@class='scope c-gray-aset']/a/text()")
        if company_scope:
            company_scope = "|".join(company_scope)
        else:
            logger.error("提取company_scope失败, company_id: %s" % company_id)
            company_scope = ""
        company_round = response.xpath("//span[@class='t-small c-green']/text()")
        if company_round:
            company_round = company_round[0]
            company_round = company_round.replace("\n", "").replace("\t", "")
        else:
            logger.error("提取company_round失败, company_id: %s" % company_id)
            company_round = ""
        company_slogan = response.xpath("//h2[@class='seo-slogan']/text()")
        if company_slogan:
            company_slogan = company_slogan[0]
        else:
            logger.error("提取company_slogan失败, company_id: %s" % company_id)
            company_slogan = ""

        company_intro_xpaths = ["//div[@class='summary'][2]/text()", "//div[@class='abstract']/text()",
                                "//div[@class='summary']/text()", "//div[@class='desc']/text()",
                                "//div[@class='introduction'][2]/text()"]
        company_intro = None
        for company_intro_xpath in company_intro_xpaths:
            intro = response.xpath(company_intro_xpath)
            if intro:
                company_intro = intro[0]
        if company_intro is None:
            logger.error("提取company_intro失败, company_id: %s" % company_id)
            company_intro = ""

        company_tags = response.xpath("//a/span[@class='tag']/text()")
        if company_tags:
            company_tags = "|".join(company_tags)
        else:
            logger.error("提取company_tags失败, company_id: %s" % company_id)
            company_tags = ""
        company_area = response.xpath("//span[@class='loca c-gray-aset']/a/text()")
        if company_area:
            company_area = "|".join(company_area)
            company_area = company_area.replace("\n", "").replace("\t", "")
        else:
            logger.error("提取company_area失败, company_id: %s" % company_id)
            company_area = ""
        company_launch_time = response.xpath("//div[@class='des-more']/div[2]/h2[@class='seo-second-title'][1]/text()")
        if company_launch_time:
            company_launch_time = company_launch_time[0]
        else:
            logger.error("提取company_launch_time失败, company_id: %s" % company_id)
            company_launch_time = ""
        company_people_num = response.xpath("//div[@class='des-more']/div[2]/h2[@class='seo-second-title'][2]/text()")
        if company_people_num:
            company_people_num = company_people_num[0]
            company_people_num = company_people_num.replace("\n", "").replace("\t", "")
        else:
            logger.error("提取company_people_num失败, company_id: %s" % company_id)
            company_people_num = ""
        company_status = response.xpath("//div[@class='des-more']/div[3]/span/text()")
        if company_status:
            company_status = company_status[0]
        else:
            logger.error("提取company_status失败, company_id: %s" % company_id)
            company_status = ""
        company_info = {
            "company_id": company_id,
            "company_name": str(company_name),
            "company_scope": str(company_scope),
            "company_round": str(company_round),
            "company_intro": str(company_intro),
            "company_tags": str(company_tags),
            "company_area": str(company_area),
            "company_launch_time": str(company_launch_time),
            "company_people_num": str(company_people_num),
            "company_status": str(company_status),
            "company_slogan": str(company_slogan),
        }

        yield company_info

    def parse_comment_company(self, response, url_filter):
        html = {
            "url": response.url,
            "html": response.text,
            "type": "user",
            "obj_id": str(response.meta["user_id"]),
            "page": response.meta["comment_page"]
        }
        if not db.select_one("select * from html WHERE url LIKE ?", "%" + response.url[5:]):
            yield html
        # yield html
        if "user_comment_company_ids" in response.meta:
            user_comment_company_ids = response.meta["user_comment_company_ids"]
        else:
            user_comment_company_ids = []
        company_urls = response.xpath("//ul[@class='list-timeline-flow with-min-height']/li/p/a/@href")
        if company_urls:
            for company_url in company_urls:
                # https://www.itjuzi.com/company/61394
                yield Request(url=str(company_url), callback=self.parse_company_info)
                try:
                    company_id = re.fullmatch("https*://www.itjuzi.com/company/(\d+)", company_url).group(1)
                    company_id = int(company_id)
                    # company_ids.append(company_id)
                    user_comment_company_ids.append(company_id)
                except AttributeError:
                    logger.error("无法是用正则表达式从company_url中提取到company_id, company_url: %s" % company_url)
                pass
        if len(company_urls) == 10:
            if response.meta.get("comment_page_num", None) is not None:
                comment_page_num = response.meta["comment_page_num"]
            else:
                count = response.xpath(
                    "//div[@class='titlebar bg-gray']/div[@class='tabset card-style']/a[@class='tab on']/span/text()")
                if count:
                    count = int(count[0][1:-1])
                    comment_page_num = count / 10 + 1
                else:
                    comment_page_num = None
                    logger.error("无法提取用户行为数据的总数")
            if comment_page_num is not None:
                if response.meta["comment_page"] < comment_page_num:
                    next_page = response.meta["comment_page"] + 1
                    next_page_url = response.url.split("?")[0] + "?page=%d" % next_page
                    response.meta["user_comment_company_ids"] = user_comment_company_ids
                    response.meta["comment_page"] = next_page
                    response.meta["comment_page_num"] = comment_page_num
                    yield Request(url=next_page_url, meta=response.meta, callback=self.parse_comment_company)
                    # if page <= page_num:
                    #     parse_user_active(user_id, active_type, page)
        user_info = response.meta["user_info"]
        user_info["user_follow_company_ids"] = ",".join(
            [str(company_id) for company_id in response.meta["user_follow_company_ids"]])
        user_info["user_history_company_ids"] = ",".join(
            [str(company_id) for company_id in response.meta["user_history_company_ids"]])
        user_info["user_comment_company_ids"] = ",".join([str(company_id) for company_id in user_comment_company_ids])
        yield user_info

    def parse_user_follow(self, response, url_filter):
        # print(response.meta)
        if "user_follow_company_ids" in response.meta:
            user_follow_company_ids = response.meta["user_follow_company_ids"]
        else:
            user_follow_company_ids = []
        company_urls = response.xpath("//ul[@class='list-commen-withpic with-min-height']/"
                                      "li/div[@class='picinfo']/div[@class='right']/sapn[@class='titel']/a/@href")
        if company_urls:
            for company_url in company_urls:
                # https://www.itjuzi.com/company/61394
                yield Request(url=str(company_url), callback=self.parse_company_info)
                try:
                    company_id = re.fullmatch("https*://www.itjuzi.com/company/(\d+)", company_url).group(1)
                    company_id = int(company_id)
                    # company_ids.append(company_id)
                    user_follow_company_ids.append(company_id)
                except AttributeError:
                    logger.error("无法是用正则表达式从company_url中提取到company_id, company_url: %s" % company_url)
                pass
        if len(company_urls) == 10:
            if response.meta.get("follow_page_num", None) is not None:
                follow_page_num = response.meta["follow_page_num"]
            else:
                count = response.xpath(
                    "//div[@class='titlebar bg-gray']/div[@class='tabset card-style']/a[@class='tab on']/span/text()")
                if count:
                    count = int(count[0][1:-1])
                    follow_page_num = count / 10 + 1
                else:
                    follow_page_num = None
                    logger.error("无法提取用户行为数据的总数")
            if follow_page_num is not None:
                if response.meta["follow_page"] < follow_page_num:
                    next_page = response.meta["follow_page"] + 1
                    next_page_url = response.url.split("?")[0] + "?page=%d" % next_page
                    response.meta["user_follow_company_ids"] = user_follow_company_ids
                    response.meta["follow_page"] = next_page
                    response.meta["follow_page_num"] = follow_page_num
                    yield Request(url=next_page_url, meta=response.meta, callback=self.parse_user_follow)
                    # if page <= page_num:
                    #     parse_user_active(user_id, active_type, page)
        response.meta["user_follow_company_ids"] = user_follow_company_ids
        history_url = "https://www.itjuzi.com/user/get_follow_history/%s" % response.meta["user_info"]["user_id"]
        response.meta["history_page"] = 1
        yield Request(url=history_url, callback=self.parse_user_history, meta=response.meta)

    def parse_user_history(self, response, url_filter):

        html = {
            "url": response.url,
            "html": response.text,
            "type": "user",
            "obj_id": str(response.meta["user_id"]),
            "page": response.meta["history_page"]
        }
        if not db.select_one("select * from html WHERE url LIKE ?", "%" + response.url[5:]):
            yield html
        # yield html

        if "user_history_company_ids" in response.meta:
            user_history_company_ids = response.meta["user_history_company_ids"]
        else:
            user_history_company_ids = []
        company_urls = response.xpath("//ul[@class='list-commen-withpic with-min-height']/"
                                      "li/div[@class='picinfo']/div[@class='right']/sapn[@class='titel']/a/@href")
        if company_urls:
            for company_url in company_urls:
                # https://www.itjuzi.com/company/61394
                yield Request(url=str(company_url), callback=self.parse_company_info)
                try:
                    company_id = re.fullmatch("https*://www.itjuzi.com/company/(\d+)", company_url).group(1)
                    company_id = int(company_id)
                    # company_ids.append(company_id)
                    user_history_company_ids.append(company_id)
                except AttributeError:
                    logger.error("无法是用正则表达式从company_url中提取到company_id, company_url: %s" % company_url)
                pass
        if len(company_urls) == 10:
            if response.meta.get("history_page_num", None) is not None:
                history_page_num = response.meta["history_page_num"]
            else:
                count = response.xpath(
                    "//div[@class='titlebar bg-gray']/div[@class='tabset card-style']/a[@class='tab on']/span/text()")
                if count:
                    count = int(count[0][1:-1])
                    history_page_num = int(count / 10 + 1)
                else:
                    history_page_num = None
                    logger.error("无法提取用户行为数据的总数")
            if history_page_num is not None:
                if response.meta["history_page"] < history_page_num:
                    next_page = response.meta["history_page"] + 1
                    next_page_url = response.url.split("?")[0] + "?page=%d" % next_page
                    response.meta["user_history_company_ids"] = user_history_company_ids
                    response.meta["history_page"] = next_page
                    response.meta["history_page_num"] = history_page_num
                    yield Request(url=next_page_url, meta=response.meta, callback=self.parse_user_history)
                    # if page <= page_num:
                    #     parse_user_active(user_id, active_type, page)
        response.meta["user_history_company_ids"] = user_history_company_ids

        url = "https://www.itjuzi.com/user/get_user_comment/%s" % response.meta["user_info"]["user_id"]
        response.meta["comment_page"] = 1
        yield Request(url=url, callback=self.parse_comment_company, meta=response.meta)


class JuziSaver(Saver):
    def __init__(self, spider_name):
        super(JuziSaver, self).__init__(spider_name)
        user_file = "user.json"
        company_file = "company.json"
        self.user_fp = open(user_file, "a", encoding="utf-8")
        self.company_fp = open(company_file, "a", encoding="utf-8")
        self.user_id_fp = open("user_id_save.txt", "a", encoding="utf-8")
        self.company_id_fp = open("company_id_save.txt", "a", encoding="utf-8")

        db.create_engine("root", "123456", "itjuzi", "127.0.0.1", "3306", charset="utf8")

    def process_item(self, item, spider_name):
        # raise Exception("这是一个测试middleware的Exception")
        # print(item)
        # print(type(item))
        json_str = json.dumps(item) + "\n"

        if "user_id" in item:
            print(item)
            # self.user_fp.write(json_str)
            db.insert("user", **item)
            # self.user_id_fp.write(str(item["user_id"]) + "\n")
            # self.user_id_fp.flush()
            # self.user_fp.flush()
            USER_SAVE_IDS.add(str(item["user_id"]))
            # print(USER_SAVE_IDS)
        if "company_id" in item:
            print(item)
            db.insert("company", **item)
            # self.company_fp.write(json_str)
            # self.company_id_fp.write(str(item["company_id"]) + "\n")
            # self.company_id_fp.flush()
            # self.company_fp.flush()
            COMPANY_SAVE_IDS.add(str(item["company_id"]))
            # print(COMPANY_SAVE_IDS)
        if "url" in item:
            try:
                db.insert("html", **item)
            except IntegrityError as e:
                if "Duplicate entry" in str(e):
                    print(e)

    def close(self):
        self.user_fp.close()
        self.company_fp.close()
        self.user_id_fp.close()
        self.company_id_fp.close()


class ItjuziSqlSaver(MysqlSaver):
    def process_item(self, item, spider_name):
        pass


if __name__ == '__main__':
    parser = ItJuziParser("juzi")
    downloader = DownLoader(spider_name="juzi", encoding="utf-8", retry_times=1)
    saver = JuziSaver("juzi")
    spider = WebSpider(spider_name="juzi", downloader_cls=downloader, parser_cls=parser, saver_cls=saver)

    # start_url = "https://www.itjuzi.com/user/1"
    headers1 = headers
    headers1["Referer"] = "https://www.itjuzi.com"
    for i in range(1,10000):
        headers1["Referer"] = "https://www.itjuzi.com/user/%d" %i
        url = "https://www.itjuzi.com/user/get_follow_company/%d"%i
        spider.add_a_task("download", (1, Request(url=url, headers=headers1, meta={"follow_page": 1, "user_id": i})))

    # spider.add_a_task("download", (1, Request(url=start_url, meta={"follow_page": 1, "user_id": 74038})))

    spider.start(downloader_num=1, parser_num=1, saver_num=1)
