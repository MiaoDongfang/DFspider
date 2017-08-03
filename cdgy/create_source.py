#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import re
from DFspider.util import html_utils
from DFspider.util.html_utils import remove_blank
from DFspider.util import db

__author__ = "dong fang"

if __name__ == '__main__':
    db.create_engine("root", "123456", "pachong")

    count = db.select('select count(*) as count_num from article')[0]["count_num"]
    num = int(count / 1000)
    for i in range(num + 1):
        if i < num:
            start = i * 1000
        else:
            start = num * 1000
        articles = db.select("select articleId, content from article limit ?,1000", start)
        # articles = db.select("select articleId, content from article WHERE releaseDate<'2017-02-01 00:00:00'")
        print(len(articles))
        for index, article in enumerate(articles):
            print("正在处理第" + str(start + index) + "条")
            content = html_utils.filter_tags(article["content"])
            html_content = html_utils.remove_blank(html_content)
            pattern = re.compile("\./.*?\.[A-Za-z1-9]+")
            result = pattern.match(html_content)
            if result:
                html_content = html_content[result.span()[1]:]
            source = content[:120]
            db.update("update article set source=? WHERE articleId=?", source, article["articleId"])
