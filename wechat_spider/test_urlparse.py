#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib.parse

__author__ = "East"
__created__ = "2017/4/13 22:20"

url = "/mp/getappmsgext?__biz=MzAxOTU0OTY0OA==&appmsg_type=9&mid=2649843935&sn=4ef5802abbb4b1011ba8e69fccc45ef3&" \
      "idx=4&scene=0&title=%E3%80%90%E5%85%AC%E7%A4%BA%E5%85%AC%E5%91%8A%E3%80%912016%E5%B9%B4%" \
      "E5%B9%BF%E5%B7%9E%E5%BC%80%E5%8F%91%E5%8C%BA%E5%88%9B%E4%B8%9A%E5%92%8C%E5%88%9B%E6%96%B0%E9%A2%8" \
      "6%E5%86%9B%E4%BA%BA%E6%89%8D%E6%8B%9F%E5%85%A5%E9%80%89%E5%90%8D%E5%8D%95&ct=1492079591&abtest_cookie=AQ" \
      "ABAAsAAQCOhh4AAAA=&devicetype=android-19&version=/mmbizwap/zh_CN/htmledition/js/appmsg/index350caa.js&f=" \
      "json&r=0.4312634146772325&is_need_ad=1&comment_id=1145275357&is_need_reward=0&both_ad=1&reward_uin_coun" \
      "t=0&msg_daily_idx=1&uin=777&key=777&pass_ticket=60whCihZqyLbUvwPZabIcZkfd%25252F0%25252FY32XfEQIMbSY%25" \
      "252FikfP2DtnV5toPNOqtmnlcBt&wxtoken=1817566955&devicetype=android-19&clientversion=26050632&x5=0&f=json"

params = urllib.parse.urlparse(url)
rs = urllib.parse.parse_qs(params.query)
print(rs.get('sn'))
