#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import urllib.parse
import re
import json
import time

from flask import Flask
from flask import request

from DFspider.util import db

__author__ = "dong fang"

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
    print("GetWxHistoryList")
    db.update("delete from tmplist WHERE `load`=?", 1)
    items = db.select("select id, content_url from post WHERE content is NULL ")
    if items:
        url = items[0]["content_url"]
    else:
        with db.transaction():
            items = db.select("select * from weixin ORDER BY last_time limit 0,1")
            db.update("update weixin set collect=? WHERE `id`=?", time.time(), items[0]["id"])
            # if items[0]["collect"] - time.time() < (60 * 60 * 12):
            #     url = ""
            # else:
            biz = items[0]["biz"]
            # url = "http://mp.weixin.qq.com/mp/getmasssendmsg?__biz=" \
            #       + biz + "#wechat_webview_type=1&wechat_redirect"  # 拼接公众号历史消息url地址（第一种页面形式）
            url = "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=" \
                  + biz + "&scene=124#wechat_redirect"  # 拼接公众号历史消息url地址（第二种页面形式）
    time.sleep(2)
    return "<script>setTimeout(function(){window.location.href='" + url + "';},2000);</script>"


@app.route("/get_next_article")
def get_next_article():
    print("get_next_article")
    db.update("delete from tmplist WHERE `load`=?", 1)
    items = db.select("select id, content_url from post WHERE content is NULL ")
    if len(items) > 1:
        url = items[0]["content_url"]
    else:
        with db.transaction():
            items = db.select("select * from weixin ORDER BY last_time limit 0,1")
            db.update("update weixin set collect=? WHERE `id`=?", time.time(), items[0]["id"])
            # if items[0]["collect"] - time.time() < 60 * 60 * 60 * 12:
            #     url = ""
            # else:
            biz = items[0]["biz"]
            # url = "http://mp.weixin.qq.com/mp/getmasssendmsg?__biz=" \
            #       + biz + "#wechat_webview_type=1&wechat_redirect"  # 拼接公众号历史消息url地址（第一种页面形式）
            url = "https://mp.weixin.qq.com/mp/profile_ext?action=home&__biz=" \
                  + biz + "&scene=124#wechat_redirect"  # 拼接公众号历史消息url地址（第二种页面形式）
    time.sleep(2)
    return "<script>setTimeout(function(){window.location.href='" + url + "';},2000);</script>"


@app.route("/process_article", methods=["post"])
def process_article():
    print("process_article")
    response = urllib.parse.unquote(request.form["str"])
    url = urllib.parse.unquote(request.form["url"])
    print(url)
    biz = get_url_query(url, "__biz")
    sn = get_url_query(url, "sn")
    article_id = db.select("select id from post WHERE biz=? and content_url like '%" + sn + "%' limit 0,1", biz)
    if len(article_id) == 1:
        article_id = article_id[0]["id"]
        with db.transaction():
            db.update("update post set `content`=? WHERE `id`=?", response, article_id)
            db.update("delete from tmplist WHERE content_url like '%" + sn + "%'")
    return "success"


@app.route("/process_history_list", methods=["POST"])
def process_history_list():
    print("ProcessHistoryList")
    json_str = urllib.parse.unquote(request.form["str"])
    url = urllib.parse.unquote(request.form["url"])
    #
    biz = get_url_query(url, "__biz")
    if is_in_db(biz, "weixin", "biz"):
        pass
    else:
        db.insert("weixin", **{"biz": biz, "collect": time.time()})
    json_str.replace('&quot;', "'")
    pattern = re.compile("&quot;")
    json_str = pattern.sub('"', json_str)

    articles = json.loads(json_str)["list"]
    print(len(articles))
    for article in articles:
        article_type = article["comm_msg_info"]["type"]
        if article_type == 49:
            content_url = (article["app_msg_ext_info"]["content_url"]).replace("\\", "")
            is_multi = article['app_msg_ext_info']['is_multi']  # 是否是多图文消息
            datetime = article['comm_msg_info']['datetime']  # 图文消息发送时间
            if not is_in_db(content_url, "post", "content_url"):
                # db.insert("tmplist", **{"content_url": content_url})
                fileid = article['app_msg_ext_info']['fileid']  # 一个微信给的id
                title = article['app_msg_ext_info']['title']  # 文章标题
                print(title)
                # title_encode = urllib.parse.urlencode(title.replace("&nbsp;", ""))  # 建议将标题进行编码，这样就可以存储emoji特殊符号了
                digest = article['app_msg_ext_info']['digest']  # 文章摘要
                source_url = (article['app_msg_ext_info']['source_url']).replace("\\", "")  # 阅读原文的链接
                cover = (article['app_msg_ext_info']['cover']).replace("\\", "")  # 封面图片
                is_top = 1  # 标记一下是头条内容
                db.insert("post", **{"biz": biz, "field_id": fileid, "title": title,
                                     "digest": digest, "content_url": content_url, "source_url": source_url,
                                     "cover": cover, "is_multi": is_multi, "is_top": is_top, "datetime": datetime})
                print("文章标题: %s" % title)
            if is_multi == 1:
                multi_articles = article['app_msg_ext_info']['multi_app_msg_item_list']
                for multi_article in multi_articles:
                    content_url = multi_article["content_url"].replace("\\", "")
                    if not is_in_db(content_url, "post", "content_url"):
                        # db.insert("tmplist", **{"content_url": content_url})
                        title = multi_article["title"]
                        fileid = multi_article['fileid']  # 一个微信给的id
                        # title_encode = urllib.parse.urlencode(title.replace("&nbsp;", ""))
                        digest = multi_article['digest']  # 文章摘要
                        source_url = multi_article['source_url'].replace("\\", "")  # 阅读原文的链接
                        cover = multi_article["cover"].replace("\\", "")  # 封面图片
                        db.insert("post",
                                  **{"biz": biz, "field_id": fileid, "title": title,
                                     "digest": digest, "content_url": content_url, "source_url": source_url,
                                     "cover": cover, "is_multi": is_multi, "is_top": is_top, "datetime": datetime})
                        print("文章标题: %s" % title)

    return "success"


@app.route("/process_read_and_like_count", methods=["POST"])
def process_read_and_like_count():
    print("ProcessReadAndLikeCount")
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
