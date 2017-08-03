#!/usr/bin/env python
# -*- coding: utf-8 -*-


import copy
import queue
import threading
from datetime import datetime

from mysql.connector.errors import Error
from mysql.connector.errors import IntegrityError

from ..models import Request
from ..util import db
from ..util.log import logger
from ..util.url_filter import UrlFilter
from ..workers import DownLoaderWorker, SaverWorker, ParserWorker, MonitorThread

# from parser import Parser

__author__ = "dong fang"


class ThreadPool(object):
    def __init__(self, spider_name, downloader_cls, parser_cls, saver_cls, parsed_save="file",
                 parsed_save_file_name=None, parsed_save_table=None,
                 url_filter=UrlFilter(),
                 monitor_sleep_time=5):
        self.spider_name = spider_name
        self.downloader = downloader_cls
        self.parser = parser_cls
        self.saver = saver_cls

        self.download_queue = queue.PriorityQueue()  # (priority, spider_name, {url=url, method=method.....})
        self.save_queue = queue.Queue()  # (priority, spider_name, item)
        self.parse_queue = queue.PriorityQueue()  # (priority, spider_name, response)

        self.state_count_dict = {
            "task_running_count": 0,
            "not_download": 0,
            "not_save": 0,
            "not_parse": 0,
            "success_downloaded": 0,
            "success_parsed": 0,
            "success_saved": 0,

            "fail_downloaded": 0,
            "ignore_downloaded": 0,
            "fail_parsed": 0,
            "fail_saved": 0,
        }
        self.url_filter = url_filter
        self.state_dict_lock = threading.Lock()

        self.downloaded_fp_lock = threading.Lock()

        self.monitor_stop = False
        self.monitor = MonitorThread(name="spider", pool=self, sleep_time=monitor_sleep_time,
                                     spider_name=spider_name)
        self.monitor.setDaemon(True)
        self.monitor.start()

        self.parse_save = parsed_save
        if parsed_save == "file":
            if parsed_save_file_name is not None:
                self.parse_fp = open(parsed_save_file_name)
            else:
                self.parse_fp = open("parsed.txt", "w", encoding="utf-8")

    # @staticmethod
    # def _init_downloaded_urls_file():
    #     urls = set()
    #     if os.path.exists("downloaded.txt"):
    #         try:
    #             fp = open("downloaded.txt", "r")
    #             urls = [url.replace("\n", "") for url in fp.readlines()]
    #         except IOError as e:
    #             logger.exception(e)
    #             urls = set()
    #     return set(urls)
    #
    # @staticmethod
    # def _init_downloaded_urls_db():
    #     try:
    #         results = db.select("select url from downloaded_url")
    #         urls = [item["url"] for item in results]
    #         logger.debug(urls)
    #         return set(urls)
    #     except Exception as e:
    #         logger.exception(e)
    #         logger.fatal("从数据库中获得下载过的url失败,请检查程序")
    #         raise e

    def start_request(self, start_urls):
        if isinstance(start_urls, (list, tuple)):
            for url in start_urls:
                if isinstance(url, str):
                    self.add_a_task("download", (0, Request(url=url, callback="parse", dont_filter=True)))
                elif isinstance(url, Request):
                    self.add_a_task("download", (0, start_urls))
                else:
                    logger.error()
        elif isinstance(start_urls, str):
            self.add_a_task("download", (0, Request(url=start_urls, callback="parse", dont_filter=True)))
        elif isinstance(start_urls, Request):
            self.add_a_task("download", (0, start_urls))

    def add_a_task(self, task_class, task):
        if task_class == "download":
            if task[1].dont_filter:
                self.download_queue.put(task, block=True)
                self._update_state_dict("not_download", 1)
            else:
                if self.url_filter.check(task[1].url):
                    self.download_queue.put(task, block=True)
                    self._update_state_dict("not_download", 1)
                else:
                    logger.warning("%s 已经被下载或在黑名单中, 忽略" % task[1].url)
                    # print(self.url_filter.url_set)
        if task_class == "save":
            self.save_queue.put(task, block=True)
            self._update_state_dict("not_save", 1)
        if task_class == "parse":
            self.parse_queue.put(task, block=True)
            self._update_state_dict("not_parse", 1)

    def update_url_downloaded_file(self, url):
        self.downloaded_fp_lock.acquire()
        with open("downloaded.txt", "a") as fp:
            fp.write(url + "\n")
        self.downloaded_fp_lock.release()

    @staticmethod
    def update_db(url, table):
        try:
            url["create_time"] = (str(datetime.now())).split(".")[0]
            db.insert(table, **url)
        except IntegrityError:
            logger.info("数据库中已经有该url，%s" % url)
        except Error as e:
            logger.error(str(e))
            logger.exception(e)
            logger.error("downloaded url保存数据库失败，%s" % url)

    def finish_a_task(self, task_class, task, is_success):
        if task_class == "download":
            if is_success:
                self._update_state_dict("success_downloaded", 1)
                # self.update_db({"url": task[0], "is_success": 1, "status_code": task[1], "refer": task[2]},
                #                "downloaded_url")
            else:
                self._update_state_dict("fail_downloaded", 1)
                # self.update_db({"url": task[0], "is_success": 0, "status_code": task[1], "refer": task[2]},
                #                "downloaded_url")
            # self.downloaded_urls.add(task)
            self.download_queue.task_done()
            self._update_state_dict("task_running_count", -1)
        elif task_class == "save":
            if is_success:
                self._update_state_dict("success_saved", 1)
            else:
                self.state_count_dict["fail_saved"] += 1
                self._update_state_dict("fail_saved", 1)
            self.save_queue.task_done()
            self._update_state_dict("task_running_count", -1)
        elif task_class == "parse":
            if callable(task[0].callback):
                callback = task[0].callback.__name__
            else:
                callback = task[0].callback if task[0].callback else "parse"
            if is_success:
                self._update_state_dict("success_parsed", 1)

                if self.parse_save == "file":
                    self.parse_fp.write(task[0].url + "\n")
                elif self.parse_save == "db":
                    self.update_db(
                        {"url": task[0].url, "is_success": 1, "callback": callback, "fail_reason": task[1]},
                        "parsed")
            else:
                self._update_state_dict("fail_parsed", 1)
                # self.update_db(
                #     {"url": task[0].url, "is_success": 0, "callback": callback, "fail_reason": task[1]},
                #     "parsed")
            self.parse_queue.task_done()
            self._update_state_dict("task_running_count", -1)
        else:
            logger.error("没有'%s'类任务" % task_class)

    def get_a_task(self, task_class):
        task = None
        if task_class == "download":
            task = self.download_queue.get(block=True, timeout=5)
            self._update_state_dict("not_download", -1)
            self._update_state_dict("task_running_count", 1)
        elif task_class == "save":
            task = self.save_queue.get(block=True, timeout=5)
            self._update_state_dict("not_save", -1)
            self._update_state_dict("task_running_count", 1)
        elif task_class == "parse":
            task = self.parse_queue.get(block=True, timeout=5)
            self._update_state_dict("not_parse", -1)
            self._update_state_dict("task_running_count", 1)
        else:
            logger.error("没有'%s'类任务" % task_class)
        return task

    def _update_state_dict(self, key, value):
        self.state_dict_lock.acquire()
        self.state_count_dict[key] += value
        self.state_dict_lock.release()

    def start(self, downloader_num=10, parser_num=3, saver_num=3, is_over=True):
        logger.warning("{class_name} start: fetcher_num={fetcher_num}, is_over={is_over}".format(
            class_name=self.__class__.__name__, fetcher_num=downloader_num, is_over=is_over))

        download_workers = [
            DownLoaderWorker("downloader_%s_%d" % (self.spider_name, i), copy.deepcopy(self.downloader),
                             self, self.spider_name) for i in range(downloader_num)]
        parser_workers = [
            ParserWorker("parser_%s_%d" % (self.spider_name, i), self.parser, self,
                         self.spider_name) for i in range(parser_num)]
        saver_workers = [
            SaverWorker("saver_%s_%d" % (self.spider_name, i), self.saver, self,
                        self.spider_name) for i in range(saver_num)]
        thread_list = download_workers + list(parser_workers) + list(saver_workers)

        for thread in thread_list:
            thread.setDaemon(True)
            thread.start()

        for thread in thread_list:
            if thread.is_alive():
                thread.join()

        if is_over and self.monitor.is_alive():
            self.monitor_stop = True
            self.monitor.join()

        for thread in thread_list:
            thread.close()

        logger.warning("{class_name} end: fetcher_num={downloader_num}, is_over={is_over}".format(
            class_name=self.__class__.__name__, downloader_num=downloader_num, is_over=is_over))

    def all_task_done(self):
        flag = self.state_count_dict["not_download"] or self.state_count_dict["not_save"] or \
               self.state_count_dict["not_parse"] or self.state_count_dict["task_running_count"]
        return flag

    def close(self):
        self.parse_fp.close()


if __name__ == '__main__':
    pass
