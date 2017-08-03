#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import urllib.parse
import re
import json
import time
import random
from datetime import datetime

# third-part library
import requests
from flask import Flask
from flask import request
from lxml import html
from lxml import etree

# my library
from DFspider.util import db
from DFspider.util.config_util import CONFIG_USERAGENT_ALL
from DFspider.util.log import logger
from DFspider.util.html_utils import fix_html

__author__ = "dong fang"

IMAGE_DIRECTORY = '/mnt/static_files/images/'

app = Flask(__name__)


def is_in_db(value, table, field):
    item = db.select("select * from " + table + " WHERE " + field + "=?", value)
    return bool(item)


def get_url_query(url, query):
    """

    :param url:
    :param query:
    :return:
    """
    parse_result = urllib.parse.urlparse(url)
    querys = urllib.parse.parse_qs(parse_result.query)
    value = querys.get(query)
    if value:
        return value[0]
    else:
        return None


@app.route("/get_history_list")
def get_history_list():
    logger.info("正在获取下一个url")
    db.update("delete from tmplist WHERE `load`=?", 1)
    db.update("delete from tmplist WHERE content_url is NULL or content_url = ''")
    if db.select("select id from tmplist"):
        with db.transaction():
            items = db.select("select * from tmplist limit 0,1")
            db.update("update tmplist set `load`=1 WHERE `id`=?", items[0]["id"])
            url = items[0]["content_url"]
    else:
        with db.transaction():
            items = db.select("select * from weixin ORDER BY collect limit 0,1")
            db.update("update weixin set collect=? WHERE `id`=?", time.time(), items[0]["id"])
            biz = items[0]["biz"]
            url = "http://mp.weixin.qq.com/mp/getmasssendmsg?__biz=" \
                  + biz + "#wechat_webview_type=1&wechat_redirect"  # 拼接公众号历史消息url地址（第一种页面形式）
            url = "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=" \
                  + biz + "&scene=124#wechat_redirect"  # 拼接公众号历史消息url地址（第二种页面形式）
    return "<script>setTimeout(function(){window.location.href='" + url + "';},2000);</script>"


@app.route("/get_next_article")
def get_next_article():
    logger.info("正在获取下一个url")
    db.update("delete from tmplist WHERE `load`=?", 1)
    db.update("delete from tmplist WHERE content_url is NULL or content_url = ''")
    items = db.select("select id from tmplist")
    if len(items) > 1:
        with db.transaction():
            items = db.select("select * from tmplist limit 0,1")
            db.update("update tmplist set `load`=1 WHERE `id`=?", items[0]["id"])
            url = items[0]["content_url"]
    else:
        with db.transaction():
            items = db.select("select * from weixin ORDER BY collect limit 0,1")
            db.update("update weixin set collect=? WHERE `id`=?", time.time(), items[0]["id"])
            biz = items[0]["biz"]
            url = "http://mp.weixin.qq.com/mp/getmasssendmsg?__biz=" \
                  + biz + "#wechat_webview_type=1&wechat_redirect"  # 拼接公众号历史消息url地址（第一种页面形式）
            url = "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=" \
                  + biz + "&scene=124#wechat_redirect"  # 拼接公众号历史消息url地址（第二种页面形式）
    return "<script>setTimeout(function(){window.location.href='" + url + "';},2000);</script>"


@app.route("/process_article", methods=["post"])
def process_article():
    logger.info("正在处理文章内容页面")
    response = urllib.parse.unquote(request.form["str"])
    url = urllib.parse.unquote(request.form["url"])
    print(url)
    tree = html.fromstring(response)
    content = tree.xpath("//div[@id='js_content']")
    if content:
        images = content[0].xpath("//img")
        headers = {"Host": "mmbiz.qpic.cn", "Upgrade-Insecure-Requests": '1',
                   "User-Agent": random.choice(CONFIG_USERAGENT_ALL)}
        for image in images:
            src = image.xpath("@data-src")
            if src:
                src = src[0]
                resp = requests.get(src, headers=headers)
                if resp.status_code == requests.codes.ok:
                    wx_fmt = get_url_query(src, "wx_fmt")
                    if wx_fmt is None:
                        wx_fmt = 'png'
                    image_name = db.next_id() + '.' + wx_fmt
                    logger.info("正在下载图片 %s" % src)
                    with open("%s%s" % (IMAGE_DIRECTORY, image_name), "wb") as fp:
                        fp.write(resp.content)
                    logger.info("图片下载成功")
                    image.set("src", "../images/" + image_name)
                else:
                    logger.error("图片下载失败%s" % src)
            else:
                logger.warn("无法获取图片的地址")
        content = etree.tostring(content[0], encoding="utf-8")
        content = str(content, encoding="utf-8")
        content = content.replace("amp;", "")
        content = fix_html(content)
    else:
        logger.error("提取文章内容失败%s" % url)
        content = None
    author = tree.xpath("//div[@id='js_profile_qrcode']/div/strong[@class='profile_nickname']/text()")
    if author:
        author = author[0]
    else:
        logger.error("提取文章作者(公众号)失败")
        author = ""
    author = str(author)
    biz = get_url_query(url, "__biz")
    sn = get_url_query(url, "sn")
    articles = db.select("select * from post WHERE biz=? and content_url like '%" + sn + "%' limit 0,1", biz)
    if len(articles) == 1:
        article = articles[0]
        with db.transaction():
            db.update("update post set `content`=?, author=? WHERE `id`=?", content, author, article["id"])
            db.update("delete from tmplist WHERE content_url like '%" + sn + "%'")
            weixin = db.select("select * from weixin WHERE biz=?", article["biz"])
            if content is None or content == "" or article["title"] == "" or article["title"] is None:
                logger.error("文章的标题或内容未空，舍弃该文章")
            else:
                logger.info("正在保存文章")
                if author == "":
                    author = weixin[0]["name"]
                article_lk = {
                    "collectionId": weixin[0]["id"],
                    "channelId": weixin[0]["channelId"],
                    "title": article["title"],
                    "content": content,
                    "releaseDate": article["datetime"],
                    "author": author,
                    "source": article["digest"],
                    "status": "release",
                    "createUser": "admin",
                    "hotSpot": 0,
                    "dataType": weixin[0]["dataType"],
                    "location": weixin[0]["location"],
                    "createDate": (str(datetime.now())).split(".")[0],
                }
                db.insert("article", **article_lk)
                logger.info("文章保存成功")
    return "success"


@app.route("/process_history_list", methods=["POST"])
def process_history_list():
    logger.debug("正在处理文章历史页面")
    json_str = urllib.parse.unquote(request.form["str"])
    url = urllib.parse.unquote(request.form["url"])
    #
    biz = get_url_query(url, "__biz")
    if is_in_db(biz, "weixin", "biz"):
        pass
    else:
        last_id = db.select("select id from weixin ORDER BY id DESC limit 0,1 ")
        if last_id:
            next_id = last_id[0]["id"] + 1
        else:
            next_id = 10001
        db.insert("weixin", **{"id": next_id, "biz": biz, "collect": time.time()})
    json_str.replace('&quot;', "'")
    pattern = re.compile("&quot;")
    json_str = pattern.sub('"', json_str)

    articles = json.loads(json_str)["list"]
    for article in articles:
        article_type = article["comm_msg_info"]["type"]
        if article_type == 49:
            content_url = (article["app_msg_ext_info"]["content_url"]).replace("\\", "")
            is_multi = article['app_msg_ext_info']['is_multi']  # 是否是多图文消息
            release_date = article['comm_msg_info']['datetime']  # 图文消息发送时间
            dt = time.localtime(release_date)
            release_date = time.strftime("%Y-%m-%d %H:%M:%S", dt)
            if (not is_in_db(content_url, "tmplist", "content_url")) and \
                    (not is_in_db(content_url, "post", "content_url")):
                db.insert("tmplist", **{"content_url": content_url})
                fileid = article['app_msg_ext_info']['fileid']  # 一个微信给的id
                title = article['app_msg_ext_info']['title']  # 文章标题
                # title_encode = urllib.parse.urlencode(title.replace("&nbsp;", ""))  # 建议将标题进行编码，这样就可以存储emoji特殊符号了
                digest = article['app_msg_ext_info']['digest']  # 文章摘要
                source_url = (article['app_msg_ext_info']['source_url']).replace("\\", "")  # 阅读原文的链接
                cover = (article['app_msg_ext_info']['cover']).replace("\\", "")  # 封面图片
                is_top = 1  # 标记一下是头条内容
                db.insert("post", **{"biz": biz, "field_id": fileid, "title": title,
                                     "digest": digest, "content_url": content_url, "source_url": source_url,
                                     "cover": cover, "is_multi": is_multi, "is_top": is_top, "datetime": release_date})
                logger.info("正在抓取文章, 文章标题：%s" % title)
            if is_multi == 1:
                multi_articles = article['app_msg_ext_info']['multi_app_msg_item_list']
                for multi_article in multi_articles:
                    content_url = multi_article["content_url"].replace("\\", "")
                    if (not is_in_db(content_url, "tmplist", "content_url")) and \
                            (not is_in_db(content_url, "post", "content_url")):
                        db.insert("tmplist", **{"content_url": content_url})
                        title = multi_article["title"]
                        fileid = multi_article['fileid']  # 一个微信给的id
                        # title_encode = urllib.parse.urlencode(title.replace("&nbsp;", ""))
                        digest = multi_article['digest']  # 文章摘要
                        source_url = multi_article['source_url'].replace("\\", "")  # 阅读原文的链接
                        cover = multi_article["cover"].replace("\\", "")  # 封面图片
                        is_top = 0
                        db.insert("post",
                                  **{"biz": biz, "field_id": fileid, "title": title,
                                     "digest": digest, "content_url": content_url, "source_url": source_url,
                                     "cover": cover, "is_multi": is_multi, "is_top": is_top, "datetime": release_date})
                        logger.info("正在抓取文章, 文章标题：%s" % title)

    return "success"


@app.route("/process_read_and_like_count", methods=["POST"])
def process_read_and_like_count():
    print("ProcessReadAndLikeCount")
    logger.info("正在处理文章的点赞和阅读数量")
    # json_str = urllib.parse.unquote(request.form["str"])
    # url = urllib.parse.unquote(request.form["url"])
    # print(url)
    # biz = get_url_query(url, "__biz")
    # sn = get_url_query(url, "sn")
    #
    # item = json.loads(json_str)
    # like_num = item["appmsgstat"]["like_num"]
    # read_num = item["appmsgstat"]["read_num"]
    #
    # article_id = db.select("select id from post WHERE biz=? and content_url like '%" + sn + "%' limit 0,1", biz)
    # if article_id:
    #     article_id = article_id[0]["id"]
    #     db.update("update post set like_num=?, read_num=? WHERE id=?", like_num, read_num, article_id)
    #     db.update("delete from post WHERE id=?", article_id)
    # print(json_str)
    # print(json_str)
    # print("====================")
    # print(url)
    return "success"


if __name__ == "__main__":
    db.create_engine(user="root", password="123456", database="pachong")
    app.run(port=8080)
