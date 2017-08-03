#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

import requests
import magic

__author__ = "dong fang"

if __name__ == '__main__':
    resp = requests.get("http://dgetb.dg.gov.cn/dgetbWebLib/UploadFiles/ViewFile.aspx?ID=8379")
    # m = magic.Magic(magic_file="share/magic", mime=False)
    print(magic.from_buffer(resp.content))
    print(resp.content)
