#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from functools import total_ordering

__author__ = "dong fang"

__all__ = ["Request"]


@total_ordering
class Request(requests.Request):
    def __init__(self, url=None, method='GET', headers=None, files=None, data=None, dont_filter=False,
                 params=None, auth=None, cookies=None, hooks=None, json=None, meta=None, callback=None,
                 ua=None, proxies=None, stream=None, verify=None, cert=None, timeout=10, retry_times=None,
                 allow_redirects=True, sleep_time=0):
        requests.Request.__init__(self, method=method, url=url, headers=headers, files=files,
                                  data=data, params=params, auth=auth, cookies=cookies, hooks=hooks, json=json)
        self.meta = meta or {}
        self.callback = callback
        self.ua = ua
        self.proxies = proxies
        self.stream = stream
        self.verify = verify
        self.cert = cert
        self.timeout = timeout
        self.allow_redirects = allow_redirects
        self.retry_times = retry_times
        self.dont_filter = dont_filter
        self.sleep_time = sleep_time

        self.request_dict = {
            "method": method,
            "url": url,
            "headers": headers or {},
            "files": files,
            "data": data,
            "params": params,
            "auth": auth,
            "cookies": cookies,
            "hooks": hooks,
            "json": json,
            "meta": self.meta,
            "callback": self.callback,
            "ua": self.ua,
            "proxies": self.proxies,
            "stream": self.stream,
            "verify": self.verify,
            "cert": self.cert,
            "timeout": self.timeout,
            "allow_redirects": self.allow_redirects,
            "retry_times": self.retry_times,
            "sleep_time": self.sleep_time,
        }

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
