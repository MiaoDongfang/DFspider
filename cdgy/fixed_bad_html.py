#!/usr/bin/env python
# -*- coding: utf-8 -*-

from DFspider.util.html_utils import fix_html
from DFspider.util import db

__author__ = "East"
__created__ = "2017/4/8 23:20"

if __name__ == '__main__':
    db.create_engine("root", "183902", "pachong")

    articles = db.select("select articleId,content from article WHERE author='四川省知识产权局'")

    for index, article in enumerate(articles):
        print("正在处理第" + str(index) + "条")
        content = fix_html(article["content"])
        db.update("update article set content=? WHERE articleId=?", content, article["articleId"])
    print("处理完成")

