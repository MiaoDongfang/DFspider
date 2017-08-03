#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import urllib.parse
import re
import os
from datetime import datetime
import json

# Third-Party Library
import requests
from lxml import etree
import mysql.connector.errors

# My Library
from DFspider.spiders import WebSpider
from DFspider.instances import DownLoader, Parser, MysqlSaver
from DFspider.models import Request
from DFspider.util import db
from DFspider.util.log import logger
from DFspider.util.url_filter import get_url_filter
from DFspider.util.config_util import CONFIG_URLPATTERN_FILES
from DFspider.configs import configs
from DFspider.util.date_format import date_format
from DFspider.util.html_utils import filter_tags
from DFspider.util.db import next_id
from DFspider.errors import ParserError, DownloaderError, OverTimeError
from DFspider.util.html_utils import fix_html

__author__ = "East"
__created__ = "2017/3/16 21:10"

# 从日志之文件中读取附件的保存地址
file_configs = configs.get("file")
APPENDIX_DOWNLOADED_DIR = file_configs.get("appendix_downloaded_dir")
if APPENDIX_DOWNLOADED_DIR is None:
    APPENDIX_DOWNLOADED_DIR = "appendix_downloaded_dir"
# 如果目标路径不存在   则创建
if not os.path.exists(APPENDIX_DOWNLOADED_DIR):
    os.makedirs(APPENDIX_DOWNLOADED_DIR)


def remove_content(content, remove_regx):
    """
    根据正则表达式移除字符串中与正则表达式匹配的内容
    :param content: 需要操作的字符串
    :param remove_regx: 正则表达式
    :return:  返回修改后的字符串
    """
    remove_pattern = re.compile(remove_regx, re.IGNORECASE)
    con = remove_pattern.sub("", content)
    return con


def download_file(request, appendix_dir, refer):
    """
    下载文件，并将相应的信息存储到数据库中
    :param request:  下载的request
    :param appendix_dir: 附件存储的文件夹
    :param refer: refer地址
    :return: 如果下载并保存成功则返回文件名
              如果因为文件的下载路径过长导致无法保存到数据库，则返回文件名，同时记录错误日志
              如果下载失败，则抛出DownloaderError异常
    """
    # 初始化下载器
    dl = DownLoader(spider_name="lianke", encoding="utf-8", retry_times=0)
    file_name = next_id()
    file_type = request.url.split("/")[-1].split(".")[-1]
    file_name = file_name + "." + file_type
    file_path = appendix_dir + "/" + file_name
    try:
        resp = dl.download(request)
        with open(file_path, "wb") as fp:
            fp.write(resp.content)
        create_time = (str(datetime.now())).split(".")[0]
        url = request.url
        if len(request.url) >= 255:
            url = file_path
        db.insert("downloaded_url",
                  **{"url": url, "status_code": resp.status_code, "create_time": create_time, "refer": refer,
                     "type": "appendix", "cache_path": file_path})
        return file_name
    except DownloaderError:
        logger.error("文件下载失败, url: %s, refer:%s" % (request.url, refer))
        raise DownloaderError("文件下载失败")
    except mysql.connector.errors.Error as e:
        logger.exception(e)
        logger.error("downloaded_url保存失败，可能是url过长")
        return file_name


def download_file2(request, appendix_dir, refer, file_type=None):
    """
    功能同download_file（可优化合并两个方法） 当文件扩展名不能从url中获取时调用此方法
    :param request:  http request请求
    :param appendix_dir: 附件保存路径
    :param refer:  refer地址，解决源网站防盗链的问题
    :param file_type:  默认为None，当为None时自动从http response headers中获取文件的扩展名
    :return: 返回文件名或抛出异常
    """
    dl = DownLoader(spider_name="lianke", encoding="utf-8", retry_times=0)
    file_name = next_id()

    try:
        resp = dl.download(request)
        # print(resp.headers)
        if file_type is None:
            if "Content-Disposition" in resp.headers:
                file_type = resp.headers["Content-Disposition"].split("filename=")[1].split(".")[-1]
            else:
                return None
        file_name = file_name + "." + file_type
        file_path = appendix_dir + "/" + file_name
        with open(file_path, "wb") as fp:
            fp.write(resp.content)
        create_time = (str(datetime.now())).split(".")[0]
        url = request.url
        if len(request.url) >= 255:
            url = file_path
        db.insert("downloaded_url",
                  **{"url": url, "status_code": resp.status_code, "create_time": create_time, "refer": refer,
                     "type": "appendix", "cache_path": file_path})
        return file_name
    except DownloaderError:
        logger.error("文件下载失败, url: %s, refer:%s" % (request.url, refer))
        return None
    except mysql.connector.errors.Error:
        logger.error("downloaded_url保存失败，可能是url过长")
        return file_name


def replace_path_and_download(html_content, response):
    """
    替换html页面中的图片和附件为绝对路径或是本地路径
    :param html_content:
    :param response:
    :return:
    """
    link_pattern = re.compile(r'(<a.*?href=")(.*?)(".*?/a>)', re.I)
    img_pattern = re.compile(r'(<img.*?\Wsrc=")(.*?)(".*?>)')

    def replace(m):
        match_url = m.group(2)
        if "://" not in match_url:  # 不含://来的链接是相对路径
            if not match_url.startswith("../appendixes/"):
                match_url = urllib.parse.urljoin(response.url, match_url)
        # 如果是文件则下载
        file_url_pattern = re.compile(CONFIG_URLPATTERN_FILES, flags=re.IGNORECASE)
        if file_url_pattern.search(match_url):
            try:
                logger.info("正在下载附件 %s" % match_url)
                file_name = download_file(
                    Request(url=match_url, headers={"Referer": response.url}, meta=response.meta, timeout=8),
                    APPENDIX_DOWNLOADED_DIR, refer=response.url)
                if file_name is not None:
                    match_url = "../appendixes/" + file_name
                    logger.info("附件下载成功，将附件下载地址替换为本地地址")
            except DownloaderError:
                logger.error("附件下载失败")

            except Exception as e:
                logger.error("附件下载失败")
                logger.exception(e)
        return m.group(1) + match_url + m.group(3)

    content = link_pattern.sub(replace, html_content)
    content = img_pattern.sub(replace, content)

    return content


class CdgySpider(Parser):
    """
    Parser类
    """
    def parse(self, response, url_filter):
        """
        parse方法  用于提取文章的url 和递归的翻页抓取
        :param response: http response对象
        :param url_filter: url_filter对象
        :return:
        """
        # 从response中将meta信息提取出来
        meta = response.meta

        # 从meta中取出各种爬取规则
        rules = meta.get("rules")
        article_url_xpath = rules.get("articleUrlXpath")
        article_root_url = rules.get("articleRootUrl")
        article_url_regex = rules.get("articleUrlRegx")
        list_article_release_date_xpath = rules.get("listArticleReleaseDateXpath")
        list_article_release_date_regx = rules.get("listArticleReleaseDateRegx")
        release_date_begin = rules.get("releaseDateBegin")

        # 把从数据库中取到的字符串格式的日期转换为date
        if release_date_begin is not None:
            try:
                release_date_begin = date_format(release_date_begin)
            except Exception as e:
                logger.error("无法转换日期，格式不正确 release_date_begin:%s" % release_date_begin)
                logger.exception(e)
                release_date_begin = None
        # 列表页的日期格式
        list_article_release_date_pattern = rules.get("listArticleReleaseDatePattern")

        # 用于存放文章的url
        article_urls = []
        # 标识是否抓取下一页
        crawl_next_page = True

        # 提取文章连接地址
        # 可考虑只是用正则表达式  正则表达式的通用性更强
        # 如果规则中有xpath表达式则使用xpath表达式提取
        if article_url_xpath is not None and article_url_xpath != "":
            article_urls = response.xpath(article_url_xpath)
        # 如果是正则表达式 则使用正则表达式提取
        elif article_url_regex is not None and article_url_regex != "":
            extract_url_pattern = re.compile(article_url_regex)
            article_urls = extract_url_pattern.findall(response.text)

        # 提取列表页中的文章发布日期  同样是两种提取方式  xpath表达式和正则表达式
        # list_article_release_date = None
        if list_article_release_date_xpath is not None and list_article_release_date_xpath != "":
            list_article_release_date = response.xpath(list_article_release_date_xpath)
        elif list_article_release_date_regx is not None and list_article_release_date_regx != "":
            list_article_release_date_regex_pattern = re.compile(list_article_release_date_regx)
            list_article_release_date = list_article_release_date_regex_pattern.findall(response.text)
        else:
            list_article_release_date = []

        # 根据提取到文章url 循环抓取文章
        for index, article_url in enumerate(article_urls):

            # 拼接文章的绝对url地址
            #  针对四川省财政厅的url拼接方式
            if response.url.startswith("http://www.sccz.gov.cn"):
                article_url = article_root_url + article_url
            # 常规的文章地址拼接方式
            else:
                article_url = urllib.parse.urljoin(article_root_url, article_url)
            # 网站http://www.sccz.gov.cn中的url含有汉字 需要经过编码才能使url_filter正常
            if article_url.startswith('http://www.sccz.gov.cn'):
                article_url = urllib.parse.quote(article_url, safe=(58, 63, 38, 47, 61))
            # 判断这些article_urls 是否都已经爬取过， 如果有已经爬取过不需要爬下一页，反之要爬下一页
            # 此功能暂时未开 可能会导致爬虫不稳定  待优化
            if not url_filter.check(article_url):
                # 用于标识是否抓取下一页
                # crawl_next_page = False
                logger.warn("文章%s 已经被下载或在黑名单中, 忽略" % article_url)
            else:
                # 只有当文章的文章发布日期列表与文章url列表长度相同
                # 列表页日期的正则表达式被定义
                # release_date_begin定义
                # 时才判断日期是否在抓取日期内
                if len(list_article_release_date) == len(
                        article_urls) and list_article_release_date_pattern is not None and \
                                list_article_release_date_pattern != '' and release_date_begin is not None:
                    # 把release_date 转换为日期类型
                    release_date = self._get_release_date(list_article_release_date[index],
                                                          list_article_release_date_pattern)
                    # 如果将日期字符串正常转化日期类型
                    # 这一段当时测试时meta信息传递较乱 可考虑优化
                    if release_date is not None:
                        # 在抓取时间范围内即抓取，反之舍弃文章，不抓取
                        if release_date > release_date_begin:
                            meta2 = response.meta
                            meta2["article_release_date"] = release_date
                            meta2["priority"] = 2
                            # 生成request 交给spider抓取
                            yield Request(url=article_url, headers={"refer": response.url}, callback=self.parse_article,
                                          meta=meta2,
                                          dont_filter=True, sleep_time=response.sleep_time)
                        else:
                            logger.warning("文章发布日期不在范围内，舍弃文章，%s" % release_date)
                    else:
                        meta3 = response.meta
                        meta3["priority"] = 2
                        # 生成request 交给spider抓取
                        yield Request(url=article_url, headers={"refer": response.url}, callback=self.parse_article,
                                      meta=meta3,
                                      dont_filter=True, sleep_time=response.sleep_time)
                else:
                    # 生成request 交给spider抓取
                    yield Request(url=article_url, headers={"refer": response.url}, callback=self.parse_article,
                                  meta=response.meta,
                                  dont_filter=True, sleep_time=response.sleep_time)

        # 翻页抓取
        if crawl_next_page:
            # 如果有next page的url则直接翻页抓取
            # 获取各种翻页规则
            next_page_button_xpath = rules.get("nextPageButtonXpath")
            next_page_root_url = rules.get("nextPageRootUrl")
            last_page_url = response.meta.get("last_page_url")
            next_page_url_xpath = rules.get("nextPageUrlXpath")

            # 提取总页数的规则  当初为了全量抓取才定义了该规则，在增量抓取过程中其实用处不大
            # 后期优化中可以考虑去掉该规则，手动定义总页数即可
            total_page_regx = rules.get("totalPageRegx")
            total_page_xpath = rules.get("totalPageXpath")
            total_page = rules.get("totalPage")

            # 如果定义了翻页按钮的xpath表达式，则根据xpath表达式提取下一页的url并抓取
            if next_page_button_xpath is not None and next_page_button_xpath != "":
                next_page_url = response.xpath(next_page_button_xpath)
                # 获取页码信息 控制翻页
                page = meta.get("page")
                page = 1 if page <= 0 else page
                next_page = page + 1
                page_end = rules.get("pageEnd")

                # 如果下一页的url提取成功
                if next_page_url:
                    next_page_url = next_page_url[0]
                    #  如果定义了page_end 则抓取的页数为page_end
                    if page_end is not None and isinstance(page_end, int) and page_end != 0:
                        if next_page < page_end:
                            if next_page_url != last_page_url and next_page_url:
                                meta["last_page_url"] = next_page_url
                                meta["page"] = next_page
                                meta["priority"] = 1
                                next_page_url = urllib.parse.urljoin(next_page_root_url, next_page_url)
                                yield Request(url=next_page_url, callback="parse", meta=meta,
                                              sleep_time=response.sleep_time, dont_filter=True)
                            else:
                                logger.warn("下一页已经被抓取过，或者已是最后一页")
                    # 否则全部抓取
                    else:
                        if next_page_url != last_page_url and next_page_url:
                            meta["last_page_url"] = next_page_url
                            meta["priority"] = 1
                            next_page_url = urllib.parse.urljoin(next_page_root_url, next_page_url)
                            yield Request(url=next_page_url, callback="parse", meta=meta,
                                          sleep_time=response.sleep_time, dont_filter=True)
                        else:
                            logger.warn("下一页已经被抓取过，或者已是最后一页")
                else:
                    logger.error("无法根据xpath获取下一页的url, url:{url}, xpath:{xpath}".format(url=response.url,
                                                                                       xpath=next_page_button_xpath))

            # 主要针对工业信息化部网站其分页的链接全部在首页，故可以一次性取出进行抓取
            elif next_page_url_xpath is not None and next_page_url_xpath != "":
                next_page_urls = response.meta.get("next_page_urls")
                page_end = rules.get("pageEnd")
                # 如果所有的分页信息在meta中，则不用再次获取所有的分页链接
                if next_page_urls is not None and isinstance(next_page_urls, (list, tuple)):
                    page = response.meta.get("page")
                    next_page = page - 1
                    if page_end is not None and page_end != 0 and isinstance(page_end, int):
                        page_end = min(page_end, len(next_page_urls))
                    else:
                        page_end = len(next_page_urls)
                    meta["page"] = next_page
                    meta["priority"] = 1
                    if abs(next_page) < page_end:
                        url = urllib.parse.urljoin(next_page_root_url, next_page_urls[next_page])
                        yield Request(url=url, callback="parse", meta=meta, dont_filter=True,
                                      sleep_time=response.sleep_time)
                # 否则需要获取放入分页信息，并将其放入meta中
                else:
                    next_page_urls = response.xpath(next_page_url_xpath)
                    meta["next_page_urls"] = next_page_urls
                    meta["page"] = -1
                    meta["priority"] = 1
                    if next_page_urls:
                        url = urllib.parse.urljoin(next_page_root_url, next_page_urls[-1])
                        yield Request(url=url, callback="parse", meta=meta, dont_filter=True,
                                      sleep_time=response.sleep_time)

            # 无法从列表页直接提取下一页的url时，需要根据相应的规则生成下一页的url

            elif (total_page_regx is not None and total_page_regx != "") or (
                            total_page_xpath is not None and total_page_xpath != "") or (
                            total_page is not None and total_page != ""):
                page_count = meta.get("page_count")
                # 如果已经提取过总页数，则直接跳过提取总页数的步骤
                if page_count is None:
                    # 爬取的页数
                    page_count = 0

                    #  获取需要爬取的页数
                    #  获取相应的规则
                    # total_page_regx = rules.get("totalPageRegx")
                    # total_page_xpath = rules.get("totalPageXpath")
                    total_page = rules.get("totalPage")
                    page_end = rules.get("pageEnd")

                    # 如果定义了page_end则总页数直接为page_end
                    if page_end is not None and page_end != "":
                        page_count = int(page_end)
                    else:
                        # 如果定义了提取总页数的xpath表达式则通过xpath提取
                        if total_page_xpath is not None and total_page_xpath != "":
                            page_count = response.xpath(total_page_xpath)
                            if page_count:
                                try:
                                    page_count = int(page_count[0].strip())
                                except ValueError as e:
                                    logger.exception(e)
                                    logger.fatal("通过xpath表达式提取的total_count无法转换为数字，"
                                                 "请检查xpath是否正确,%s" % total_page_xpath)
                        else:
                            # 否则如果定义了提取总页数的正则表达式，则按照正则提取，正则是从整个网页源代码中提取
                            if total_page_regx is not None and total_page_regx != "":
                                pattern = re.compile(total_page_regx)
                                result = pattern.search(response.text)
                                print(result.group(1))
                                if result:
                                    try:
                                        page_count = int(result.group(1).strip())
                                    except ValueError as e:
                                        logger.exception(e)
                                        logger.fatal("通过正则表达式提取的total_count无法转换为数字，"
                                                     "请检查正则表达式是否正确,%s" % total_page_xpath)
                                    except AttributeError as e:
                                        logger.exception(e)
                                        logger.error("无法提取total_page，请检查正则表达式是否正确 %s" % total_page_regx)
                            else:
                                # 否则如果定义了total_page字段则按照total_page作为总页数
                                if total_page is not None and total_page != "":
                                    page_count = int(total_page)
                    # 如果通过以上的方法没有提取到总页数  则默认page_count为10
                    if page_count <= 0:
                        page_count = 10
                else:
                    pass
                # 把总页数信息放入response和request的meta中， 以便下次判断是否提取总页数
                meta["page_count"] = page_count
                meta["priority"] = 1
                # 获取上次爬取的页码
                page = int(response.meta.get("page"))
                next_page = page + 1
                # 如果next_page小于总页数则继续爬取，否则不爬取
                if next_page < page_count:
                    # 把next_page信息放入meta中
                    meta["page"] = next_page
                    # 获取下一页的相关信息
                    method = rules.get("nextPageRequestMethod")
                    next_page_post_params = rules.get("nextPagePostParams")
                    next_page_post_url = rules.get("nextPagePostUrl")
                    next_page_get_url = rules.get("nextPageGetUrl")
                    page_article_count = rules.get("pageArticleCount")

                    # 如果翻页参数是文章数量时
                    if page_article_count is not None:
                        page_article_count = int(page_article_count)
                        next_page = next_page * page_article_count
                    if method is not None and method != "":
                        method = method.upper()
                    if method == "GET" or method is None or method == "":
                        if next_page_get_url != "" and next_page_get_url is not None:
                            next_page_get_url = next_page_get_url.format(page=next_page)
                            next_page_get_url = urllib.parse.urljoin(article_root_url, next_page_get_url)
                            yield Request(url=next_page_get_url, callback="parse", meta=meta, dont_filter=True,
                                          sleep_time=response.sleep_time)
                        else:
                            logger.warn("下一页的地址或get参数不正确, %s" % next_page_get_url)
                    elif method.upper() == "POST":
                        if next_page_post_url != "" and next_page_post_url is not None \
                                and next_page_post_params is not None and next_page_post_params != "":
                            params_str = next_page_post_params.format(page=next_page)
                            params_strs = params_str.split(",")
                            params = {param.split(":")[0]: param.split(":")[1] for param in params_strs}
                            yield Request(url=next_page_post_url, method="POST", params=params,
                                          callback="parse", meta=meta, dont_filter=True, sleep_time=response.sleep_time)
                        else:
                            logger.warn("下一页的POST地址或POST参数正确")
                    else:
                        logger.warn("无法获取下一页")
            else:
                logger.info("没有定义相关的翻页参数")
        else:
            logger.debug("下一页已经抓取过")

    @staticmethod
    def _get_release_date(article_release_date, article_release_date_regx):
        """
        根据时间字符串获得发布日期
        :param article_release_date:   时间字符串
        :param article_release_date_regx:  正则表达式  第一个分组提取原始日期， 第2，3，4，5，6，7组分别是年月日时分秒
        :return:  返回一个时间字符串
        """
        if article_release_date_regx is not None and article_release_date_regx != "":
            date_pattern = re.compile(article_release_date_regx)
            search_result = date_pattern.search(article_release_date)
            if search_result is not None:
                # release_date = search_result.group(1)
                release_date_year = None
                release_date_month = None
                release_date_day = None
                release_date_hour = None
                release_date_minute = None
                release_date_second = None
                try:
                    release_date_year = search_result.group(2)
                    release_date_month = search_result.group(3)
                    release_date_day = search_result.group(4)
                    if len(release_date_year) == 2:
                        release_date_year = "20" + release_date_year
                        # release_date = datetime(release_date_year, release_date_month, release_date_day)
                except IndexError:
                    logger.error("发布日期的正则表达式不正确，请注意分组,%s" % article_release_date_regx)
                except AttributeError:
                    logger.error(
                        "没有匹配到任何日期信息，请检查正则表达式%s与日期字符串%s是否正确" % (article_release_date_regx, article_release_date))
                try:
                    release_date_hour = search_result.group(5)
                    release_date_minute = search_result.group(6)
                except IndexError:
                    pass

                try:
                    release_date_second = search_result.group(7)
                except IndexError:
                    pass

                if release_date_year is not None and release_date_month is not None and release_date_day is not None:
                    try:
                        if release_date_hour is not None and release_date_minute is not None:
                            if release_date_second is not None:
                                release_date = datetime(int(release_date_year), int(release_date_month),
                                                        int(release_date_day),
                                                        int(release_date_hour), int(release_date_minute),
                                                        int(release_date_second))
                            else:
                                release_date = datetime(int(release_date_year), int(release_date_month),
                                                        int(release_date_day),
                                                        int(release_date_hour), int(release_date_minute))
                        else:
                            release_date = datetime(int(release_date_year), int(release_date_month),
                                                    int(release_date_day))
                        release_date = release_date
                    except TypeError:
                        logger.error("日期转换错误，请检查正则表达式及分组是否正确")
                        release_date = None
                else:
                    logger.error("文章发布日期获取失败，请检查正则表达式是否正确%s" % article_release_date_regx)
                    release_date = None
                return release_date
            else:
                logger.error("没有匹配到任何日期信息,请检查正则表达式是否正确")
                return None
        else:
            logger.error("正则表达式为空，自动把日期字符串赋值为空字符串''")
            return None

    def parse_article(self, response, url_filter):
        """

        :param response:
        :param url_filter:
        :return:
        """
        rules = response.meta.get("rules")
        article_title_xpath = rules.get("articleTitleXpath")
        article_title_regx = rules.get("articleTitleRegx")
        article_content_xpath = rules.get("articleContentXpath")
        article_content_regx = rules.get("articleContentRegx")
        article_release_date_xpath = rules.get("articleReleaseDateXpath")
        article_release_date_regx = rules.get("articleReleaseDateRegx")
        article_release_date_regx_total = rules.get("articleReleaseDateRegxTotal")
        release_date_begin = rules.get("releaseDateBegin")
        if release_date_begin is not None:
            try:
                release_date_begin = date_format(release_date_begin)
            except Exception as e:
                logger.error("无法转换日期，格式不正确 release_date_begin:%s" % release_date_begin)
                logger.exception(e)
                release_date_begin = None

        remove_content_regx = rules.get("removeContentRegx")

        # 提取文章日期
        # article_release_date = response.meta.get("article_release_date")
        # logger.info("article_release_date是%s" % article_release_date)
        article_release_date = None
        # if article_release_date is not None and isinstance(article_release_date, datetime):
        #     pass
        # else:
        if article_release_date_xpath is not None and article_release_date_xpath != "":
            article_release_date = response.xpath(article_release_date_xpath)
            if article_release_date:
                article_release_date = self._get_release_date(article_release_date[0], article_release_date_regx)
            else:
                logger.error("提取文章发布日期失败, url:%s" % response.url)
                article_release_date = None
        elif article_release_date_regx_total is not None and article_release_date_regx_total != "":
            article_release_date = self._get_release_date(response.text, article_release_date_regx_total)
        else:
            logger.error("提取文章发布日期失败，未定义任何的xpath和正则表达式")

        if article_release_date is not None and release_date_begin is not None:
            if article_release_date < release_date_begin:
                logger.warn("发布日期时间不在范围之内, %s " % article_release_date)
                raise OverTimeError("发布日期时间不在范围之内, %s " % article_release_date)
        else:
            pass

        if article_release_date is None:
            logger.error("没有提取到日期，舍弃该篇文章 url: %s" % response.url)
            parser_error = ParserError("没有提取到日期，舍弃该篇文章, url: %s" % response.url)
            parser_error.url = response.url
            parser_error.type = "article"
            raise parser_error

        # article_root_url = rules.get("articleRootUrl")
        # 提取文章标题
        # title = ""
        # 如果定义的是xpath表达式
        if article_title_xpath is not None and article_title_xpath != "":
            title = response.xpath(article_title_xpath)
            if title:
                # title = title[0].encode("utf-8", "ignore")
                title = ' '.join([item.strip() for item in title])
                title = title.strip()
                title = title.replace("\n", " ").replace("\r\n", " ").replace("\t", " ").replace("<br>", " ")
                title = title.encode("utf-8", "ignore")

            else:
                parser_error = ParserError("解析文章标题失败,{name},{url}".format(name=rules.get("name"), url=response.url))
                parser_error.url = response.url
                parser_error.type = "article"
                logger.error("解析文章标题失败,请检查xpath表达式是否正确,{name},{url}".format(name=rules.get("name"), url=response.url))
                raise parser_error
        # 如果定义的是正则表达式
        elif article_title_regx is not None and article_title_regx != "":
            title_pattern = re.compile(article_title_regx)
            try:
                title = title_pattern.search(response.text).group(1)
                title = title.replace("\n", " ").replace("\r\n", " ").replace("\t", " ").replace("<br>", " ")
                title = title.strip()
            except AttributeError:
                logger.error("解析文章标题失败,请检查正则表达式是否正确,{name},{url}".format(name=rules.get("name"), url=response.url))
                parser_error = ParserError(
                    "解析文章标题失败,请检查正则表达式是否正确，{name},{url}".format(name=rules.get("name"), url=response.url))
                parser_error.url = response.url
                parser_error.type = "article"
                raise parser_error
        else:
            logger.error("解析文章标题失败，未定义提取文章标题的正则表达式或xpath表达式，url:%s" % response.url)
            parser_error = ParserError(
                "解析文章标题失败，未定义提取文章标题的正则表达式或xpath表达式，url:%s" % response.url)
            parser_error.url = response.url
            parser_error.type = "article"
            raise parser_error

        if title == "" or title is None:
            logger.error(
                "解析文章标题失败,请检查xpath表达式是否正确,{name},{url}".format(name=rules.get("name"), url=response.url))
            parser_error = ParserError("解析文章标题失败,{name},{url}".format(name=rules.get("name"), url=response.url))
            parser_error.url = response.url
            parser_error.type = "article"
            raise parser_error

        # 提取文章内容
        # appendix_file_urls = []
        # appendix_files = ""
        # content = ""
        # source = ""
        # 如果定义的是xpath表达式
        if article_content_xpath is not None and article_content_xpath != "":
            content = response.xpath(article_content_xpath)
            # 正常提取到文章内容
            if content:
                # 清除文章中不必要的内容  现在只针对http://www.cdgy.gov.cn/
                # 现在可以直接在规则中定义需要删除内容的正则表达式即可  不必再添加类似的代码
                if response.url.startswith("http://www.cdgy.gov.cn/"):
                    remove_tags = content[0].xpath("//td[@height=25]")
                    # if len(remove_tags) > 0:
                    for tag in remove_tags:
                        tag.clear()

                # 特殊网站的附件下载  可以考虑在数据库中添加相应的规则
                # 四川省财政厅附件
                if response.url.startswith("http://www.sccz.gov.cn"):
                    appendixes = content[0].xpath("//td[@class='td_down']")
                    if len(appendixes) > 0:
                        # files = []
                        for appendix in appendixes:
                            down_id = appendix.xpath("@onclick")[0][11:-1]
                            root_url = "http://www.sccz.gov.cn/Site/DownAttach?id="
                            url = root_url + down_id
                            link = etree.SubElement(appendix, "a")
                            link.set("href", url)
                            file_name = appendix.xpath("text()")[0]
                            link.text = file_name
                            file_type = None
                            if re.match(".*\.[\w,\d]+", file_name):
                                file_type = file_name.split(".")[-1]
                            # if file_type is not None:
                            appendix_file_name = download_file2(
                                Request(url=url, meta=response.meta, headers={"refer": response.url},
                                        timeout=8),
                                APPENDIX_DOWNLOADED_DIR, refer=response.url, file_type=file_type)
                            if appendix_file_name is not None:
                                appendix_file_url = "../appendixes/" + appendix_file_name
                                link.set("href", appendix_file_url)
                            appendix.text = ""

                # 成都市高新区网站 附件地址的生成
                if response.url.startswith("http://www.cdht.gov.cn"):
                    appendixes = content[0].xpath("div[3]/a")
                    if len(appendixes) > 0:
                        cid = re.search("/(\d+).", response.url).group(1)
                        base_url = "http://www.cdht.gov.cn/attachment_url.jspx?cid="
                        appendix_base_url = "http://www.cdht.gov.cn/attachment.jspx?cid=" + cid + "&i="
                        n = len(appendixes)
                        req_url = base_url + cid + "&n=" + str(n)
                        json_resp = requests.get(req_url)
                        download_list = json.loads(json_resp.text)
                        for i in range(len(appendixes)):
                            appendix_url = appendix_base_url + str(i) + download_list[i]
                            print(etree.tostring(appendixes[i], encoding="utf-8"))
                            file_name = appendixes[i].xpath("text()")
                            file_type = None
                            if file_name:
                                file_name = file_name[0]
                                if re.match(".*\.[\w,\d]+", file_name):
                                    file_type = file_name.split(".")[-1]
                            appendix_file_name = download_file2(
                                Request(url=appendix_url, meta=response.meta, headers={"refer": response.url},
                                        timeout=8),
                                APPENDIX_DOWNLOADED_DIR, refer=response.url, file_type=file_type)
                            if appendix_file_name is not None:
                                appendix_file_url = "../appendixes/" + appendix_file_name
                                appendixes[i].set("href", appendix_file_url)
                            else:
                                appendixes[i].set("href", appendix_url)

                # 双创云网站 附加下载
                if response.url.startswith("http://www.shuangliusc.com"):
                    appendixes = content[0].xpath("//span[@class='down']")
                    for appendix in appendixes:
                        appendix_url = appendix.xpath("@data-fileurl")
                        appendix_name = appendix.xpath("text()")
                        link = etree.SubElement(appendix, "a")
                        link.set("href", appendix_url[0] if appendix_url else "")
                        link.text = appendix_name[0] if appendix_name else ""
                        appendix.text = ""

                # 东莞市经济和信息化局附件下载
                if response.url.startswith("http://dgetb.dg.gov.cn"):
                    appendixes = content[0].xpath(
                        "//table[@id='NewsView_Content1_dlFileList']//tr/td/table//tr/td[2]"
                        "/table//tr[1]/td[2]/span")

                    for appendix in appendixes:

                        file_id = appendix.xpath("@onclick")
                        if file_id:
                            if file_id[0].startswith("OpenFiles"):
                                file_id = file_id[0][11:-2]
                                appendix_name = appendix.xpath("text()")
                                download_root_url = "http://dgetb.dg.gov.cn/dgetbWebLib/UploadFiles/ViewFile.aspx?ID="

                                download_url = download_root_url + file_id
                                link = etree.SubElement(appendix, "a")
                                link.text = appendix_name[0] if appendix_name else ""
                                appendix_file_name = download_file2(
                                    Request(url=download_url, meta=response.meta, headers={"refer": response.url},
                                            timeout=8),
                                    APPENDIX_DOWNLOADED_DIR, refer=response.url)
                                if appendix_file_name is not None:
                                    appendix_file_url = "../appendixes/" + appendix_file_name
                                    link.set("href", appendix_file_url)
                                else:
                                    link.set("href", download_url)

                                appendix.text = ""
                            else:
                                pass

                # 提取文章内容的的html代码
                content = etree.tostring(content[0], encoding="utf-8")
                content = str(content, encoding="utf-8")
                content = content.replace("amp;", "")
            else:
                logger.error("解析文章内容失败,请检查xpath表达式是否正确,%s,%s" % (rules.get("name"), response.url))
                parser_error = ParserError(
                    "解析文章内容失败，请检查xpath表达式是否正确,%s,%s" % (rules.get("name"), response.url))
                parser_error.url = response.url
                parser_error.type = "article"
                raise parser_error

        # 根据正则表达式提取文章内容
        elif article_content_regx is not None and article_title_regx != "":
            content_pattern = re.compile(article_content_regx)
            try:
                # 提取文章内容
                content = content_pattern.search(response.text).group(1)

            except AttributeError:
                logger.error("解析文章内容失败，请检查正则表达式是否正确,%s,%s" % (rules.get("name"), response.url))
                parser_error = ParserError(
                    "解析文章内容失败，请检查正则表达式是否正确,%s,%s" % (rules.get("name"), response.url))
                parser_error.url = response.url
                parser_error.type = "article"
                raise parser_error
        else:
            logger.error("解析文章内容失败，未定义文章内容的xpath或正则表达式,%s,%s" % (rules.get("name"), response.url))
            parser_error = ParserError(
                "解析文章内容失败，未定义文章内容的xpath或正则表达式,%s,%s" % (rules.get("name"), response.url))
            parser_error.url = response.url
            parser_error.type = "article"
            raise parser_error

        # 针对菁蓉创新创业网，其文章的url每次刷新都在变化，所以需要判断文章标题和发布时间
        if response.url.startswith("http://www.cdibi.org.cn"):
            items = db.select("SELECT articleId FROM article WHERE `title`=? AND `releaseDate`=?", title,
                              article_release_date)
            if items:
                raise ParserError("该文章再数据库中已存在，舍弃该文章，菁蓉创新创业网")

        # 替换文章中的图片和超链接的相对路径为绝对路径
        # 其中附件直接下载，图片替换为源网站的地址
        content = replace_path_and_download(content, response)

        # 移除在数据库中定义的不需要的文章内容
        if remove_content_regx is not None and remove_content_regx != "":
            content = remove_content(content, remove_content_regx)

        # 修复html代码， 补全不标准的html代码  包括未闭合标签等
        content = fix_html(content)

        # 去除文章内容中的html标签，以提取文章的source
        html_content = filter_tags(content)
        html_content.replace("\n", " ").replace("\t", "").replace("\r\n", "").replace(" ", "")
        html_content.strip()
        # 去文章中的前120个字作为文章的source（摘要）
        source = html_content[:120].strip()

        article = {
            "channelId": int(rules.get("channelId")),
            "collectionId": int(rules.get("id")),
            "title": title,
            "content": content,
            "releaseDate": article_release_date,
            "author": rules.get("name"),
            "source": source,
            "status": "release",
            "createUser": "admin",
            "hotSpot": 0,
            "contentUrl": response.url,
            "dataType": rules.get("dataType"),
            "location": rules.get("location"),
            "createDate": (str(datetime.now())).split(".")[0],
        }

        # yield给save worker
        yield article


def main():
    parser = CdgySpider("lianke")
    downloader = DownLoader(spider_name="lianke", encoding="utf-8")
    saver = MysqlSaver(spider_name="lianke", user="root", pwd="123456", database="pachong", table="article",
                       host="127.0.0.1", port=3306)
    spider = WebSpider(spider_name="lianke", downloader_cls=downloader, parser_cls=parser, saver_cls=saver,
                       url_filter=get_url_filter(data_type="database", table=["parsed", "article"],
                                                 url_field_name=["url", "contentUrl"]))

    tasks = db.select("SELECT * FROM crawl_url")
    for task in tasks:
        enable = task.get("enable")
        if enable == 1:
            start_page = task.get("pageStart")
            start_page = start_page if (start_page is not None) else 1
            sleep_time = task.get("sleepTime")
            sleep_time = sleep_time if sleep_time else 0
            start_url = Request(url=task.get("url"), dont_filter=True,
                                callback="parse", meta={"rules": task, "page": start_page}, sleep_time=sleep_time)
            spider.start_request(start_url)

    spider.start(downloader_num=5, parser_num=8, saver_num=5)


def job():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def schedule_task():
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler()
    scheduler.add_job(job, "cron", day_of_week='mon-sun', hour='0,11', minute=0)
    scheduler.start()


if __name__ == '__main__':
    main()
    # schedule_task()
