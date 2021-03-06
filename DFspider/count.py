#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library


__author__ = "dong fang"

# -*- coding: utf-8 -*-
# !/usr/bin/python
# linecount.py
# 2009-1-20
# author:
#   Jason Lee
#
import sys
import os

exts = ['.py']


def read_line_count(fname):
    count = 0
    for file_line in open(fname).xreadlines():
        count += 1
    return count


if __name__ == '__main__':

    count = 0
    fcount = 0
    for root, dirs, files in os.walk(os.getcwd()):
        for f in files:
            # Check the sub directorys
            fname = (root + '/' + f).lower()
            ext = f[f.rindex('.'):]
            try:
                if (exts.index(ext) >= 0):
                    fcount += 1
                    c = read_line_count(fname)
                    count += c
            except Exception as e:
                print(e)

    print('file count:%d' % fcount)
    print('count:%d' % count)
