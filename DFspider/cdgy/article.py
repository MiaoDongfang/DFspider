#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__ = "East"
__created__ = "2017/3/16 21:15"


class Article(object):
    def __init__(self, title, content, release_date):
        self.title = title
        self.content = content
        self.release_date = release_date

    def __str__(self):
        return self.title + self.content + self.release_date


if __name__ == '__main__':
    article = Article()
    article.title = "this is a title"
    article.content = "this is content"
    article.release_date = "2017-3-15"
    print(article)
