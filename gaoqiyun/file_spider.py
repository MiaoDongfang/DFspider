#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import os
import requests
import json
import urllib.parse

__author__ = "dong fang"

file_directory = "files/"
if not os.path.exists(file_directory):
    os.makedirs(file_directory)

base_url = "http://www.hights.cn/beetl/library/list.do?showCount=15&libtype="
root_url = "http://www.hights.cn"
class_types = list(range(5))


def crawl_file_list(class_type, page=1):
    url = "%s%dcurrentPage=%d" % (base_url, class_type, page)
    resp = requests.get(url)
    return resp.text


def download_file(url: str, file_name: str):
    file_type = url.split("/")[-1]
    file_name = file_name + '.' + file_type
    file_path = file_directory + file_name
    print("正在下载文件: %s" % file_path)
    resp = requests.get(url)

    with open(file_path, "wb") as fp:
        fp.write(resp.content)
    print("下载完成")


def download_list(file_datas):
    for file_data in file_datas:
        file_url = urllib.parse.urljoin(root_url, file_data["pdfpath"])
        download_file(file_url, file_data["title"])


def main():
    for class_type in class_types:
        resp_text = crawl_file_list(class_type)
        file_dict = json.loads(resp_text)
        total_page = file_dict["reserveData"]["totalPage"]
        download_list(file_dict["data"])
        if total_page > 1:
            for i in range(2, total_page):
                resp_text = crawl_file_list(class_type)
                data_dict = json.loads(resp_text)
                download_list(data_dict["data"])


if __name__ == '__main__':
    main()
