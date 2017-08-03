#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import re
import urllib
import requests
from .config_util import CONFIG_URLPATTERN_FILES
from bs4 import BeautifulSoup


__author__ = "dong fang"


def replace_char_entity(html_content):
    char_entities = {'nbsp': ' ', '160': ' ',
                     'lt': '<', '60': '<',
                     'gt': '>', '62': '>',
                     'amp': '&', '38': '&',
                     'quot': '"', '34': '"', }

    re_char_entity = re.compile(r'&#?(?P<name>\w+);')
    sz = re_char_entity.search(html_content)
    while sz:
        entity = sz.group()  # entity全称，如&gt;
        key = sz.group('name')  # 去除&;后entity,如&gt;为gt
        try:
            html_content = re_char_entity.sub(char_entities[key], html_content, 1)
            sz = re_char_entity.search(html_content)
        except KeyError:
            # 以空串代替
            html_content = re_char_entity.sub('', html_content, 1)
            sz = re_char_entity.search(html_content)
    return html_content


def filter_tags(html_content):
    # 先过滤CDATA
    re_cdata = re.compile('//<!\[CDATA\[[^>]*//\]\]>', re.I)  # 匹配CDATA
    re_script = re.compile('<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', re.I)  # Script
    re_style = re.compile('<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', re.I)  # style
    re_br = re.compile('<br\s*?/?>')  # 处理换行
    re_h = re.compile('</?\w+[^>]*>')  # HTML标签
    re_comment = re.compile('<!--[^>]*-->')  # HTML注释

    re_xml = re.compile("<\?.*/\?>")  # 去除xml的ms office标签

    s = re_cdata.sub('', html_content)  # 去掉CDATA
    s = re_script.sub('', s)  # 去掉SCRIPT
    s = re_style.sub('', s)  # 去掉style
    s = re_br.sub('\n', s)  # 将br转换为换行
    s = re_h.sub('', s)  # 去掉HTML 标签
    s = re_comment.sub('', s)  # 去掉HTML注释

    s = re_xml.sub("", s)
    # 去掉多余的空行
    blank_line = re.compile('\n+')
    s = blank_line.sub('\n', s)
    s = replace_char_entity(s)  # 替换实体
    return s


def remove_blank(html_content):
    blank_pattern = re.compile("\s+")
    s = blank_pattern.sub("", html_content)
    s = s.replace("\n", "").replace("\r\n", "").replace("\t", "").replace(" ", "")
    return s


def replace_relatively_to_abslute_path(html_content, base_url):
    link_pattern = re.compile(r'(<a.*?href=")(.*?)(".*?/a>)', re.I)
    img_pattern = re.compile(r'(<img.*?src=")(.*?)(".*?>)')

    def replace(m):
        match_url = m.group(2)
        if "://" not in match_url:  # 不含://来的链接是相对路径
            match_url = urllib.parse.urljoin(base_url, match_url)
        return m.group(1) + match_url + m.group(3)

    content = link_pattern.sub(replace, html_content)
    content = img_pattern.sub(replace, content)

    return content


def fix_html(html_str):
    soup = BeautifulSoup(html_str, "lxml")
    html_str = soup.prettify()
    html_str = html_str.replace("<html>", "").replace("</html>", "").replace("<body>", "").replace("</body>", "")
    return html_str
