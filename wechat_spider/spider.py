#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import urllib.parse
import json

urls = (
    '/get_history_list', 'GetWxHistoryList',
    '/process_article', 'ProcessWxArticle',
    '/process_history_list', 'ProcessHistoryList',
    '/process_read_and_like_count', 'ProcessReadAndLikeCount',

)

app = web.application(urls, globals())


class GetWxHistoryList:
    def GET(self):
        print("GetWxHistoryList")

        return "<script>setTimeout(function(){window.location.href='5623';},2000);</script>"


class ProcessWxArticle:
    def GET(self):
        print("ProcessWxArticle")
        return "success"


class ProcessHistoryList:
    def POST(self):
        print("ProcessHistoryList")
        params = web.input()
        # data = web.input()
        json_str = urllib.parse.unquote(params.get("str"))
        url = urllib.parse.unquote(params.get("url"))
        #
        # parse_result = urllib.parse.urlparse(url)
        # querys = urllib.parse.parse_qs(parse_result.query)
        # biz = querys.get("__biz")
        # json_str.replace("&quot", "")
        # articles = json.loads(json_str)
        # for article in articles:
        #     type = article["comm_msg_info"]["type"]
        #     print(article)

        print(json_str)
        print(isinstance(json_str, str))
        print(url)

        return "success"


class ProcessReadAndLikeCount:
    def POST(self):
        print("ProcessReadAndLikeCount")
        params = web.input()
        # data = web.input()
        json_str = urllib.parse.unquote(params.get("str"))
        url = urllib.parse.unquote(params.get("url"))
        print(json_str)
        print("====================")
        print(url)
        return "success"


if __name__ == "__main__":
    app.run()
