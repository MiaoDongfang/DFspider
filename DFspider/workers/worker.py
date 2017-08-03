#!/usr/bin/env python
# -*- coding: utf-8 -*-


import threading
import queue
import time
import datetime

from ..models import Request
from ..util.log import logger
from ..util.mail import send_mail2
from ..errors import DownloaderError, ParserError, OverTimeError, SaverError
from ..middlewares import ProcessDownloaderError, ProcessSaverException, ProcessParserException

__author__ = "dong fang"


class WorkerBase(threading.Thread):
    def __init__(self, name, worker, pool, spider_name):
        threading.Thread.__init__(self, name=name)
        self.worker = worker
        self.pool = pool
        self.spider_name = spider_name

    def run(self):
        logger.debug("[%s]%s start" % (self.__class__.__name__, self.getName()))
        while True:
            try:
                spider_name = self.spider_name
                self.work(spider_name)
            except queue.Empty:
                if not self.pool.all_task_done():
                    self.worker.close()
                    break
        logger.debug("[%s]%s end" % (self.__class__.__name__, self.getName()))

    def work(self, spider_name):
        raise NotImplementedError()

    def close(self):
        pass


class DownLoaderWorker(WorkerBase):

    def __init__(self, name, worker, pool, spider_name):
        super(DownLoaderWorker, self).__init__(name, worker, pool, spider_name)
        self.process_download_error = None

    def work(self, spider_name):
        # priority, request = self.pool.download_queue.get(block=True, timeout=5)
        priority, request = self.pool.get_a_task("download")
        try:
            response = self.worker.download(request)
            self.pool.add_a_task("parse", (1, response))
            self.pool.finish_a_task("download", (response.url, response.status_code, request.headers.get("refer")),
                                    True)
        except Exception as e:
            logger.exception(e)
            if isinstance(e, DownloaderError):
                self.pool.finish_a_task("download", (request.url, e.status_code, request.headers.get("refer")), False)
            else:
                self.pool.finish_a_task("download", (request.url, 0, request.headers.get("refer")), False)
                # middleware = ProcessAppendixException(request=request, exception=e)
                # middleware.process()
            self.process_download_error = ProcessDownloaderError(request, e)
            self.process_download_error.process()

        return True

    def close(self):
        if self.process_download_error is not None:
            self.process_download_error.close()


class ParserWorker(WorkerBase):

    def __init__(self, name, worker, pool, spider_name):
        super(ParserWorker, self).__init__(name, worker, pool, spider_name)
        self.process_parser_error = None

    def work(self, spider_name):
        # priority, response = self.pool.parse_queue.get(block=True, timeout=5)
        priority, response = self.pool.get_a_task("parse")
        # callback = response.callback
        try:
            self.worker.process_response(response=response, spider_name=spider_name)
            item_gen = self.worker.parse_item(response=response, spider_name=spider_name,
                                              url_filter=self.pool.url_filter)
            for item in item_gen:
                if item is not None:
                    if isinstance(item, Request):
                        priority = item.meta.get("priority", 1)
                        self.pool.add_a_task("download", (priority, item))
                    elif isinstance(item, dict):
                        self.pool.add_a_task(task_class="save", task=(priority, item))
            self.pool.finish_a_task("parse", (response, None), True)
        except OverTimeError as oe:
            self.pool.finish_a_task("parse", (response, "日期不在范围之内"), True)
            logger.info(str(oe))
            pass
        except ParserError as pe:
            self.pool.finish_a_task("parse", (response, str(pe)), True)
            logger.info(str(pe))
        except Exception as e:
            logger.exception(e)
            self.pool.finish_a_task("parse", (response, str(e)), False)
            self.process_parser_error = ProcessParserException(response, e)
            self.process_parser_error.process()
        return True

    def close(self):
        if self.process_parser_error is not None:
            self.process_parser_error.close()


class SaverWorker(WorkerBase):

    def __init__(self, name, worker, pool, spider_name):
        super(SaverWorker, self).__init__(name, worker, pool, spider_name)
        self.process_saver_error = None

    def work(self, spider_name):
        # priority, item = self.pool.save_queue.get(block=True, timeout=5)
        priority, item = self.pool.get_a_task("save")
        logger.info("正在保存: %s" % item)
        try:
            self.worker.save_item(item, spider_name)
            self.pool.finish_a_task("save", item, True)
        except Exception as e:
            logger.exception(e)
            self.pool.finish_a_task("save", item, False)
            self.process_saver_error = ProcessSaverException(item, e)
            self.process_saver_error.process()
        return True

    def close(self):
        if self.process_saver_error is not None:
            self.process_saver_error.close()


class MonitorThread(threading.Thread):
    def __init__(self, name, pool, spider_name, sleep_time=10):
        super(MonitorThread, self).__init__(name=name)
        self.pool = pool
        self.spider_name = spider_name
        self.sleep_time = sleep_time
        self.init_time = time.time()

        self.task_running_count = 0

        self.last_success_downloaded = 0
        self.last_success_parsed = 0
        self.last_success_saved = 0

        self.last_fail_downloaded = 0
        self.last_ignore_downloaded = 0
        self.last_fail_parsed = 0
        self.last_fail_saved = 0

        self.info = ""

        # 用于计算在一定时间内错误出现的数量
        self.work_run_count = 0
        self.last_work_run_count = 0
        self.last_fail_count = 0
        self.fail_count = 0

        self.start_time = datetime.datetime.now()

    def work(self):
        info_dict = self.pool.state_count_dict

        self.task_running_count = info_dict["task_running_count"]

        self.last_success_downloaded = info_dict["success_downloaded"]
        self.last_success_parsed = info_dict["success_parsed"]
        self.last_success_saved = info_dict["success_saved"]

        self.last_fail_downloaded = info_dict["fail_downloaded"]
        self.last_ignore_downloaded = info_dict["ignore_downloaded"]
        self.last_fail_parsed = info_dict["fail_parsed"]
        self.last_fail_saved = info_dict["fail_saved"]

        # fail_count = self.last_fail_parsed + self.last_fail_downloaded + self.last_fail_saved

        self.info = "爬虫: %s, %d 个线程正在运行; 成功下载 %d 个页面," \
                    "  %d 个页面下载失败; 成功解析%d个页面, %d 个页面解析失败; 成功保存 %d 个items,  " \
                    "%d 个items保存失败" % \
                    (self.spider_name, self.task_running_count, self.last_success_downloaded, self.last_fail_downloaded,
                     self.last_success_parsed, self.last_fail_parsed, self.last_success_saved, self.last_fail_saved)

        time.sleep(self.sleep_time)
        logger.info(self.info)
        # logger.info(self.pool.state_count_dict)

        return False if self.pool.monitor_stop else True

    def run(self):
        logger.debug("[%s]%s start" % (self.__class__.__name__, self.getName()))
        while True:
            if not self.work():
                self.work_run_count += 1
                break

        logger.info("[%s]%s end" % (self.__class__.__name__, self.getName()))

        self.pool.close()

        end_time = datetime.datetime.now()

        consume_time = end_time - self.start_time
        days = consume_time.days
        hours = int(consume_time.seconds / 3600)
        minutes = int((consume_time.seconds - hours * 3600) / 60)
        seconds = int(consume_time.seconds - hours * 3600 - minutes * 60)
        content = '''
            爬虫运行结束，结束时间{complete_time};
            共花费: {days}天{hours}时{minutes}分{seconds}秒;
            尝试下载{try_download_count}个网页, 成功: {success_downloaded}个, 失败:{failed_downloaded}个;
            尝试解析{try_parse_count}个网页, 成功: {success_parsed}个，失败: {failed_parse}个;
            尝试保存{try_save_count}个item, 成功: {success_saved}个，失败: {failed_save}个;
        '''
        count_dict = self.pool.state_count_dict
        content = content.format(
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            complete_time=datetime.datetime.now(),
            try_download_count=count_dict["success_downloaded"] + count_dict["fail_downloaded"],
            success_downloaded=count_dict["success_downloaded"],
            failed_downloaded=count_dict["fail_downloaded"],
            try_parse_count=count_dict["success_parsed"] + count_dict["fail_parsed"],
            success_parsed=count_dict["success_parsed"],
            failed_parse=count_dict["fail_parsed"],
            try_save_count=count_dict["success_saved"] + count_dict["fail_saved"],
            success_saved=count_dict["success_saved"],
            failed_save=count_dict["fail_saved"],
        )
        logger.info(content)
        send_mail2("本轮爬虫运行完成", content)

        logger.info(self.spider_name + "爬虫运行完成")


if __name__ == '__main__':
    start = datetime.datetime.strptime("2017-3-18 15:50:10", "%Y-%m-%d %H:%M:%S")
    print(start)
    end = datetime.datetime.now()
    consume = end - start
