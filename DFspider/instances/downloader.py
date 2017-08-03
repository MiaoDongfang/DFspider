#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library
import re
import time
import urllib.parse

# Third-Party Library
import requests
import requests.exceptions
from selenium import webdriver

# My Library
from ..models import Response, Request
from ..util import random_choice_ua
from ..configs import configs
from ..util.log import logger
from ..errors.errors import DownloaderError
from ..util import db

__author__ = "dong fang"

DOWNLOAD_SLEEP = configs.get("download_sleep", 0)
HEADERS = configs.get("headers")


class DownLoaderBase(object):
    def get(self, url, method="GET", **kwargs):
        raise NotImplementedError

    def post(self, url, method="POST", **kwargs):
        raise NotImplementedError

    def download(self, request):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError


class DownLoader(DownLoaderBase):
    def __init__(self, spider_name, session=None, encoding=None, meta=None, retry_times=3, log=None,
                 allow_redirect=True):
        # self.ua = self._init_ua()
        # self.headers = self._init_headers(headers, self.ua)
        self.ss = session if session else requests.Session()
        self.meta = meta
        # self.proxy = proxy
        self.retry_times = retry_times
        self.correct_http = 0
        self.error_http = 0
        self.log = log
        self.allow_redirect = allow_redirect
        self.spider_name = spider_name
        self.encoding = encoding

    def get(self, url, method="GET", **kwargs):
        return self.request(url, method, **kwargs)

    def post(self, url, method="POST", **kwargs):
        return self.request(url, method, **kwargs)

    def download(self, request):
        # print(type(request.url))
        result = db.select_one("select * from html WHERE url LIKE ?", "%" + request.url[5:])
        if result:
            logger.info("% 已下载，直接从数据库中取出")
            response = Response(requests.Response(), request)
            response.content = result["html"].encode("utf-8")
            response.text = result["html"]
            response.url = result["url"]
            return response
        sleep_time = request.sleep_time
        if isinstance(sleep_time, int):
            if sleep_time < DOWNLOAD_SLEEP:
                sleep_time = DOWNLOAD_SLEEP
            logger.info("下载器休眠 %d 秒" % sleep_time)
            time.sleep(sleep_time)
        else:
            logger.info("下载器休眠 %d 秒" % DOWNLOAD_SLEEP)
            time.sleep(DOWNLOAD_SLEEP)
        params = request.request_dict
        if HEADERS:
            # params["headers"] = HEADERS
            params["headers"].update(HEADERS)
        # params.__delattr__("callback")
        response = self.request(**params)
        # response = self.ss.request(**params)
        return response

    def request(self, url, method="GET", **kwargs):
        """
        :param url:
        :param method:
        :param kwargs:
        :param kwargs: ua:
        :param kwargs: proxy
        :param kwargs: headers:
        :param kwargs: params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param kwargs: data: (optional) Dictionary, bytes, or file-like object to send in the body of the :
                        class:`Request`.
        :param kwargs: headers: (optional) Dictionary of HTTP Headers to send with the :class:`Request`.
        :param kwargs: cookies: (optional) Dict or CookieJar object to send with the :class:`Request`.
        :param kwargs: files: (optional) Dictionary of ``'name': file-like-objects``
                        (or ``{'name': ('filename', fileobj)}``) for multipart encoding upload.
        :param kwargs: auth: (optional) Auth tuple to enable Basic/Digest/Custom HTTP Auth.
        :param kwargs: timeout: (optional) How long to wait for the server to send data
            before giving up, as a float, or a (`connect timeout, read timeout
            <user/advanced.html#timeouts>`_) tuple.
        :type kwargs: timeout: float or tuple
        :param kwargs: allow_redirects: (optional) Boolean. Set to True if POST/PUT/DELETE redirect
                    following is allowed.
        :type kwargs: allow_redirects: bool
        :param kwargs: proxies: (optional) Dictionary mapping protocol to the URL of the proxy.
        :param kwargs: verify: (optional) if ``True``, the SSL cert will be verified. A CA_BUNDLE path can
                        also be provided.
        :param kwargs: stream: (optional) if ``False``, the response content will be immediately downloaded.
        :param kwargs: cert: (optional) if String, path to ssl client cert file (.pem). If Tuple, ('cert', 'key') pair.
        :return:
        """

        def _get_value(key, default=None):
            return kwargs[key] if key in kwargs else default

        method = method.upper()
        if method not in ("GET", "POST"):
            raise ValueError("The request method must be 'GET' or 'POST'")
        params = _get_value("params")
        data = _get_value("data")

        # 生成request headers
        default_headers = {
            "Host": urllib.parse.urlparse(url).netloc,
            "User-Agent": random_choice_ua(),
        }

        headers = _get_value("headers", default=default_headers)
        # if headers is None:
        #     headers = default_headers
        # headers = merge_dict(default_headers, HEADERS)

        ua = _get_value("ua", None)
        if ua:
            headers.update({"User-Agent": ua})

        cookies = _get_value("cookies", None)
        files = _get_value("files", None)
        auth = _get_value("auth", None)
        timeout = _get_value("timeout", 10)
        allow_redirect = _get_value("allow_redirect", True)
        if allow_redirect != self.allow_redirect:
            allow_redirect = self.allow_redirect
        proxies = _get_value("proxy", {})
        if isinstance(proxies, str):
            proxy_pattern = re.compile("\d{1,3}\.\d{1,3}\.d{1,3}:\d{1,5}")
            if proxy_pattern.match(proxies):
                host, port = proxies.split(":")
                if int(host) <= 1024:
                    logger.warning("端口号：%s小于1024" % host)
                proxies = {'http': 'http://' + proxies, 'https': 'http://' + proxies}
            else:
                logger.warning("代理:%s不合法，自动更换为不适用代理")
                proxies = {}
        elif isinstance(proxies, dict):
            pass
        else:
            logger.warning("代理:%s不合法，自动更换为不适用代理")
            proxies = {}
        hooks = _get_value("hooks", None)
        stream = _get_value('stream', default=None)
        verify = _get_value('verify', default=None)
        cert = _get_value('cert', default=None)
        json = _get_value("json", default=None)
        meta = _get_value("meta", None)
        callback = _get_value("callback", None)
        retry_times = _get_value("retry_times", None)
        sleep_time = _get_value("sleep_time", None)
        if retry_times is not None:
            _retry_times = int(retry_times)
        else:
            _retry_times = int(self.retry_times)
        if _retry_times <= 0:
            _retry_times = 1

        self.retry_times = _retry_times

        # _retry_times += 1
        _retry_count = -1
        de = DownloaderError()
        while _retry_times:
            _retry_times -= 1
            _retry_count += 1
            # if _retry_times > 5:
            #     logger.error(u"%s 无法下载，已跳过" % url)
            #     break

            if _retry_count > 0:
                logger.warning("正在重试第%d次" % _retry_count)
            logger.debug("正在下载 %s, 代理: %s" % (url, proxies))
            status_code = 0
            try:
                # request = Request(method=method, url=url, data=data or {}, headers=headers, params=params or {})
                req = Request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    files=files,
                    data=data or {},
                    json=json,
                    params=params or {},
                    auth=auth,
                    cookies=cookies,
                    hooks=hooks,
                    meta=meta or {},
                    callback=callback,
                    sleep_time=sleep_time,
                )
                # print(req.request_dict)
                prep = self.ss.prepare_request(req)

                proxies = proxies or {}

                settings = self.ss.merge_environment_settings(
                    prep.url, proxies, stream, verify, cert
                )
                send_kwargs = {
                    'timeout': timeout,
                    'allow_redirects': allow_redirect,
                }
                send_kwargs.update(settings)
                # print(send_kwargs)
                response = self.ss.send(prep, **send_kwargs)
                # response = requests.request(method=method, url=url, **kwargs)

                if response.status_code == requests.codes.ok:
                    _retry_times = 0
                    self.correct_http = 1
                    logger.debug("<%s>下载成功  %s" % (response.status_code, url))
                    if self.encoding is not None:
                        response.encoding = self.encoding
                    status_code = response.status_code
                    return Response(response, req)
                else:
                    # self.retry_times -= 1
                    self.error_http = 1
                    logger.warning("<%s>下载失败 %s" % (response.status_code, url))
                    if 500 <= response.status_code < 600:  # 返回code为500和600之间时候是服务器的问题，故休眠1分钟
                        logger.warning('返回码为%d，休眠一分钟' % response.status_code)
                        time.sleep(10)
                    status_code = response.status_code
                    response.raise_for_status()
            except Exception as e:
                if _retry_times == 0:
                    logger.warning("<%s>下载失败 %s," % (status_code, url))
                else:
                    logger.warning("<%s>下载失败 %s,, 正在重试" % (status_code, url))
                if isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout)):
                    de.exception = "连接超时(url:%s)，无法连接到服务器或服务器无响应" % url
                else:
                    de.exception = str(e)
                de.status_code = status_code
                de.url = url
        if self.retry_times > 1:
            logger.error("已重试%d次,无法下载: %s " % (self.retry_times, url))
        else:
            logger.error("无法下载: %s " % url)
        raise de

    def get_cookie(self):
        """
        获取cookie
        :return: CookieJar
        """
        return self.ss.cookies

    def get_cookie_dict(self):
        """
        获取cookie dict
        :return: dict
        """
        return self.ss.cookies.get_dict()

    def close(self):
        pass


class BrowserDownLoader(DownLoaderBase):
    def post(self, url, method="POST", **kwargs):
        pass

    def download(self, request):
        pass

    def get(self, url, method="GET", **kwargs):
        pass

    def browse(self, url, method="GET", **kwargs):
        browser = webdriver.Chrome()
        browser.get(url)

    def close(self):
        pass

    def __ne__(self, *args, **kwargs):
        return super().__ne__(*args, **kwargs)


if __name__ == '__main__':
    dl = DownLoader("test09")
    resp = dl.get("http://www.baidu.com")
    print(dl.get_cookie())
    # resp = dl.download(
    #     Request(url="http://www.cdst.gov.cn:801/down.asp?FileName=doc/2008-7/200871093331613.doc", retry_times=0))
    # resp = requests.get("http://www.cdst.gov.cn/Type.asp?typeid=47&BigClassid=181&page=1")
    print(resp.status_code)
