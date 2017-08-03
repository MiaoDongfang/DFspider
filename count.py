#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library


__author__ = "dong fang"

import os

if __name__ == '__main__':

    count = 0
    fcount = 0
    for root, dirs, files in os.walk("cdgy"):
        for f in files:
            fname = (root + '/' + f).lower()
            if fname.endswith(".py"):
                with open(fname, "r", encoding="utf-8") as fp:
                    lines = fp.readlines()
                    count += len(lines)
                print(fname)

    print('file count:%d' % fcount)
    print('count:%d' % count)
