#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import html
from functools import total_ordering

__author__ = "dong fang"

__all__ = [
    "Request",
]

"""
    这是一个HTTP的Response类
"""


@total_ordering
class Response(object):
    def __init__(self, resp, request):
        self.resp = resp
        self.meta = request.meta or {}
        self.dont_filter = request.dont_filter
        self.callback = request.callback
        self.sleep_time = request.sleep_time
        rules = self.meta.get("rules")
        if rules is not None:
            charset = rules.get("charset")
            if charset is not None:
                self.resp.encoding = charset
            else:
                self.resp.encoding = "utf-8"
        else:
            self.resp.encoding = "utf-8"
        self.content = resp.content
        self.url = resp.url
        self.text = resp.text

    def xpath(self, xpath_exp):
        rules = self.meta.get("rules")
        if rules is not None:
            charset = rules.get("charset")
            if charset is not None:
                tree = html.fromstring(self.content.decode(charset, "ignore"))
            else:
                tree = html.fromstring(self.content.decode("utf-8", "ignore"))
        else:
            tree = html.fromstring(self.content.decode("utf-8", "ignore"))
        return tree.xpath(xpath_exp)

    # @property
    # def text(self):
    #     return self.resp.text

    # @property
    # def content(self):
    #     return self.resp.content

    # @property
    # def url(self):
    #     return self.resp.url

    @property
    def status_code(self):
        return self.resp.status_code

    @property
    def headers(self):
        return self.resp.headers

    #: File-like object representation of response (for advanced usage).
    #: Use of ``raw`` requires that ``stream=True`` be set on the request.
    # This requirement does not apply for use internally to Requests.
    @property
    def raw(self):
        return self.resp.raw

    #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
    @property
    def reason(self):
        return self.resp.reason

    #: Encoding to decode with when accessing r.text.
    @property
    def encoding(self):
        return self.resp.encoding

    @encoding.setter
    def encoding(self, value):
        # return self.resp.encoding
        self.resp.encoding = value

    #: A list of :class:`Response <Response>` objects from
    #: the history of the Request. Any redirect responses will end
    #: up here. The list is sorted from the oldest to the most recent request.
    @property
    def history(self):
        return self.resp.history

    #: A CookieJar of Cookies the server sent back.
    @property
    def cookies(self):
        return self.resp.cookies

    #: The amount of time elapsed between sending the request
    #: and the arrival of the response (as a timedelta).
    #: This property specifically measures the time taken between sending
    #: the first byte of the request and finishing parsing the headers. It
    #: is therefore unaffected by consuming the response content or the
    #: value of the ``stream`` keyword argument.
    @property
    def elapsed(self):
        return self.resp.elapsed

    def __eq__(self, other):
        if self.url == other.url:
            return True
        else:
            return False

    def __ge__(self, other):
        if self.url >= other.url:
            return True
        else:
            return False
