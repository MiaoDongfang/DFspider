#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import re
from datetime import datetime
import urllib.parse
import os

# Third-party Library
from lxml import html
from lxml import etree
import mysql.connector.errors

# My Library
from DFspider.util import db
from DFspider.util.db import next_id
from DFspider.instances import DownLoader
from DFspider.errors import DownloaderError
from DFspider.util.log import logger
from DFspider.util.config_util import CONFIG_URLPATTERN_FILES
from DFspider.configs import configs
from DFspider.models import Request
from DFspider.util.html_utils import fix_html

__author__ = "East"
__created__ = "2017/4/10 21:32"

file_configs = configs.get("file")
APPENDIX_DOWNLOADED_DIR = file_configs.get("appendix_downloaded_dir")
if APPENDIX_DOWNLOADED_DIR is None:
    APPENDIX_DOWNLOADED_DIR = "appendix_downloaded_dir"

if not os.path.exists(APPENDIX_DOWNLOADED_DIR):
    os.makedirs(APPENDIX_DOWNLOADED_DIR)


def remove_content(content, remove_regx):
    remove_pattern = re.compile(remove_regx, re.IGNORECASE)
    con = remove_pattern.sub("", content)
    return con


def download_file(request, appendix_dir, refer):
    dl = DownLoader(spider_name="lianke", encoding="utf-8", retry_times=0)
    file_name = next_id()
    file_type = request.url.split("/")[-1].split(".")[-1]
    file_name = file_name + "." + file_type
    file_path = appendix_dir + "/" + file_name
    try:
        resp = dl.download(request)
        # time.sleep(sleep_time)
        # resp = requests.get(url=url, timeout=10)
        # if resp.status_code == requests.codes.ok:
        with open(file_path, "wb") as fp:
            fp.write(resp.content)
        # create_time = (str(datetime.now())).split(".")[0]
        # url = request.url
        # if len(request.url) >= 255:
        #     url = file_path
        # db.insert("downloaded_url",
        #           **{"url": url, "status_code": resp.status_code, "create_time": create_time, "refer": refer,
        #              "type": "appendix", "cache_path": file_path})
        return file_name
    except DownloaderError:
        logger.error("文件下载失败, url: %s, refer:%s" % (request.url, refer))
        raise DownloaderError("文件下载失败")
    except mysql.connector.errors.Error as e:
        logger.exception(e)
        logger.error("downloaded_url保存失败，可能是url过长")
        return file_name


def download_file2(request, appendix_dir, refer, file_type):
    dl = DownLoader(spider_name="lianke", encoding="utf-8", retry_times=0)
    file_name = next_id()
    # file_type = request.url.split("/")[-1].split(".")[-1]
    file_name = file_name + "." + file_type
    file_path = appendix_dir + "/" + file_name
    try:
        resp = dl.download(request)
        # time.sleep(sleep_time)
        # resp = requests.get(url=url, timeout=10)
        # if resp.status_code == requests.codes.ok:
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
    except mysql.connector.errors.Error as e:
        logger.exception(e)
        logger.error("downloaded_url保存失败，可能是url过长")
        return file_name


def replace_path_and_download(html_content, response):
    link_pattern = re.compile(r'(<a.*?href=")(.*?)(".*?/a>)', re.I)
    img_pattern = re.compile(r'(<img.*?\Wsrc=")(.*?)(".*?>)')

    def replace(m):
        match_url = m.group(2)
        if "://" not in match_url:  # 不含://来的链接是相对路径
            if not match_url.startswith("../appendixes/"):
                match_url = urllib.parse.urljoin(response.url, match_url)
        file_url_pattern = re.compile(CONFIG_URLPATTERN_FILES, flags=re.IGNORECASE)
        if file_url_pattern.search(match_url):
            try:
                logger.info("正在下载附件 %s" % match_url)
                # file_name = download_file(Request(url=match_url, timeout=8),
                #                           APPENDIX_DOWNLOADED_DIR, refer=response.url)
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


def replace_content(url):
    # response = requests.get(url)
    dl = DownLoader(spider_name="lianke", encoding="utf-8", retry_times=0)
    request = Request(url=url, timeout=8)
    response = dl.download(request)
    response.encoding = "gb2312"
    tree = html.fromstring(response.text)
    content = tree.xpath("//div[@class='news_content']")
    if content:
        # 提取文章内容的的html代码
        content = etree.tostring(content[0], encoding="utf-8")
        content = str(content, encoding="utf-8")
        content = content.replace("amp;", "")

        # 替换文章中的图片和超链接的相对路径为绝对路径
        content = replace_path_and_download(content, response)
        # 移除在数据库中定义的不需要的内容
        remove_content_regx = r'(<h1.*?</h1>)|(<div\s+class="sx gary_xx_b">.*?</div>)'
        if remove_content_regx is not None and remove_content_regx != "":
            content = remove_content(content, remove_content_regx)

        # 修复html代码， 补全不标准的html代码  包括未闭合标签等
        content = fix_html(content)
    return content


def replace_url():
    db.create_engine("root", "183902", "pachong", host="112.74.45.98")

    articles = db.select(
        "SELECT articleId, content, contentUrl FROM article WHERE author='成都市科学技术局' AND title='2016年成都市第三批科技项目立项公告'")

    for index, article in enumerate(articles):
        logger.info("正在处理第" + str(index) + "条")
        if index > 145:
            url = article["contentUrl"]
            try:
                content = replace_content(url)
                if content is not None:
                    db.update("UPDATE article SET content=? WHERE articleId=?", content, article["articleId"])
            except DownloaderError as e:
                logger.exception(e)


if __name__ == '__main__':
    replace_url()
