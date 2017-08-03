#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library

# Third part library
import requests
from lxml import html
from lxml import etree

# My library
from DFspider.util import db

__author__ = "dong fang"


if __name__ == '__main__':
    db.create_engine("root", "123456", "pachong")

    articles = db.select("select articleId,content from article WHERE author='东莞市经济和信息化局'")

    for index, article in enumerate(articles):
        print("正在处理第" + str(index) + "条")
        # content = fix_html(article["content"])
        content = article["content"]
        tree = html.fromstring(content)
        appendixes = tree.xpath("//table[@id='NewsView_Content1_dlFileList']//tr/td/table//tr/"
                                "td[2]/table//tr[1]/td[2]/span")
        for appendix in appendixes:
            file_id = appendix.xpath("@onclick")
            if file_id:
                if file_id[0].startswith("OpenFiles"):
                    file_id = file_id[0][11:-2]
                    appendix_name = appendix.xpath("text()")
                    download_root_url = "http://dgetb.dg.gov.cn/dgetbWebLib/UploadFiles/ViewFile.aspx?ID="
                    # file_id = appendix[11: -2]

                    download_url = download_root_url + file_id
                    link = etree.SubElement(appendix, "a")
                    # link.set("href", download_root_url)
                    link.text = appendix_name[0] if appendix_name else ""
                    file_name = db.next_id()

                    resp = requests.get(download_url)

                    if "Content-Disposition" in resp.headers:
                        file_type = resp.headers["Content-Disposition"].split("filename=")[1].split(".")[-1]

                        file_name = file_name + "." + file_type
                        file = "/mnt/spider/appendixes/" + file_name
                        with open(file) as fp:
                            fp.write(resp.content)
                        appendix_file_url = "../appendixes/" + file_name
                        link.set("href", appendix_file_url)
                    else:
                        link.set("href", download_url)
                    appendix.text = ""

                else:
                    pass
        content = etree.tostring(tree, encoding="utf-8")
        content = str(content, encoding="utf-8")
        # print(content)
        db.update("update article set content=? WHERE articleId=?", content, article["articleId"])
    print("处理完成")

