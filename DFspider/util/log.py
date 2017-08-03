#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
import smtplib
import logging.handlers
import os

from ..configs import configs
from .mail import send_mail2

__author__ = "East"
__created__ = "2017/3/18 14:54"

# 日志文件的路径，FileHandler不能创建目录，这里先检查目录是否存在，不存在创建他
# 当然也可以继承之后重写FileHandler的构造函数
# print(configs)
log_configs = configs.get("log")
LOG_FILE_PATH = log_configs.get("log_file_path")
log_dir = os.path.dirname(LOG_FILE_PATH)
if not os.path.isdir(log_dir):
    os.mkdir(log_dir)
# 写入文件的日志等级，由于是详细信息，推荐设为debug
FILE_LOG_LEVEL = log_configs.get("file_log_level")
# 控制台的日照等级，info和warning都可以，可以按实际要求定制
CONSOLE_LOG_LEVEL = log_configs.get("console_log_level")
# 缓存日志等级，最好设为error或者critical
MEMORY_LOG_LEVEL = log_configs.get("memory_log_level")
# 致命错误等级
URGENT_LOG_LEVEL = log_configs.get("urgent_log_level")
# 缓存溢出后的邮件标题
ERROR_THRESHOLD_ACHIEVED_MAIL_SUBJECT = log_configs.get("error_threshold_achieved_mail_subject")
# 缓存溢出的阀值
ERROR_MESSAGE_THRESHOLD = log_configs.get("error_message_threshold")
# 致命错误发生后的邮件标题
CRITICAL_ERROR_ACHIEVED_MAIL_SUBJECT = log_configs.get("critical_error_achieved_mail_subject")

# 邮件服务器配置
MAIL_HOST = log_configs.get("mail_host")
MAIL_PORT = log_configs.get("mail_port")
USER = log_configs.get("user")
PASSWORD = log_configs.get("password")
FROM = log_configs.get("from")
MAIL_TO = log_configs.get("mail_to")


class OptimizeMemoryHandler(logging.handlers.MemoryHandler):
    """
       由于自带的MemoryHandler达到阀值后，每一条缓存信息会单独处理一次，这样如果阀值设的100，
      会发出100封邮件，这不是我们希望看到的，所以这里重写了memoryHandler的2个方法，
      当达到阀值后，把缓存的错误信息通过一封邮件发出去.
    """

    def __init__(self, capacity, mail_subject):
        logging.handlers.MemoryHandler.__init__(self, capacity, flushLevel=logging.ERROR, target=None)
        self.mail_subject = mail_subject
        self.flushed_buffers = []
        self.logger = logging.getLogger(__name__)

    def shouldFlush(self, record):
        """
        检查是否溢出
        """
        if len(self.buffer) >= self.capacity:
            return True
        else:
            return False

    def flush(self):
        """
         缓存溢出时的操作，
        1.发送邮件 2.清空缓存 3.把溢出的缓存存到另一个列表中，方便程序结束的时候读取所有错误并生成报告
        """
        if self.buffer != [] and len(self.buffer) >= self.capacity:
            content = ""
            for record in self.buffer:
                message = record.getMessage()
                level = record.levelname
                ctime = record.created
                t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))
                content += t + " " + "*" + level + "* : " + message + "\n"
            self.mail_notification(self.mail_subject, content)
            self.flushed_buffers.extend(self.buffer)
            self.buffer = []

    @staticmethod
    def mail_notification(subject, content):
        """
                发邮件的方法
        """
        send_mail2(subject, content)
        # msg = MIMEText(content)
        # msg['Subject'] = subject
        # msg['From'] = FROM
        # msg['To'] = ";".join(MAIL_TO)
        # try:
        #     s = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
        #     # s.connect(MAIL_HOST, 25)
        #     s.login(user=USER, password=PASSWORD)
        #     s.sendmail(FROM, MAIL_TO, msg.as_string())
        #     s.close()
        # except Exception as e:
        #     self.logger.error(str(e))


MAPPING = {"CRITICAL": 50,
           "ERROR": 40,
           "WARNING": 30,
           "INFO": 20,
           "DEBUG": 10,
           "NOTSET": 0,
           }


class MySMTPHandler(logging.handlers.SMTPHandler):
    def __init__(self, mailhost, fromaddr, toaddrs, subject, credentials=None, secure=None, timeout=5.0):
        logging.handlers.SMTPHandler.__init__(self, mailhost, fromaddr, toaddrs, subject, credentials=credentials,
                                              secure=secure, timeout=timeout)

        self.logger = logging.getLogger(__name__)

    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        from email.message import EmailMessage
        import email.utils
        msg = EmailMessage()
        msg['From'] = FROM
        msg['To'] = ";".join(MAIL_TO)
        msg['Subject'] = self.getSubject(record)
        msg['Date'] = email.utils.localtime()
        msg.set_content(self.format(record))

        try:
            s = smtplib.SMTP_SSL(MAIL_HOST, 465)
            # s.connect(MAIL_HOST, 25)
            s.login(user=USER, password=PASSWORD)
            s.sendmail(FROM, MAIL_TO, msg.as_string())
            s.close()
        except Exception as e:
            self.logger.error(str(e))


class Logger:
    """
    logger的配置
    """

    def __init__(self, log_file, file_level, console_level, memory_level, urgent_level,name="crawler"):
        # super(Logger, self).__init__(name)
        self.config(log_file, file_level, console_level, memory_level, urgent_level)

    def config(self, log_file, file_level, console_level, memory_level, urgent_level):
        # 生成root logger
        self.logger = logging.getLogger("crawler")
        self.logger.setLevel(MAPPING[file_level])
        # 生成RotatingFileHandler，设置文件大小为10M,编码为utf-8，最大文件个数为100个，如果日志文件超过100，则会覆盖最早的日志
        self.fh = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=1024 * 1024 * 10, backupCount=100,
                                                       encoding="utf-8")
        self.fh.setLevel(MAPPING[file_level])
        # 生成StreamHandler
        self.ch = logging.StreamHandler()
        self.ch.setLevel(MAPPING[console_level])
        # 生成优化过的MemoryHandler,ERROR_MESSAGE_THRESHOLD是错误日志条数的阀值
        self.mh = OptimizeMemoryHandler(ERROR_MESSAGE_THRESHOLD, ERROR_THRESHOLD_ACHIEVED_MAIL_SUBJECT)
        self.mh.setLevel(MAPPING[memory_level])
        # 生成SMTPHandler
        self.sh = MySMTPHandler((MAIL_HOST, MAIL_PORT), FROM, ";".join(MAIL_TO),
                                CRITICAL_ERROR_ACHIEVED_MAIL_SUBJECT, credentials=(USER, PASSWORD))
        self.sh.setLevel(MAPPING[urgent_level])
        # 设置格式
        formatter = logging.Formatter(
            "%(asctime)-15s *%(levelname)s* %(filename)s [line:%(lineno)d]: %(message)s", '%Y-%m-%d %H:%M:%S')
        self.ch.setFormatter(formatter)
        self.fh.setFormatter(formatter)
        self.mh.setFormatter(formatter)
        self.sh.setFormatter(formatter)
        # 把所有的handler添加到root logger中
        self.logger.addHandler(self.ch)
        self.logger.addHandler(self.fh)
        self.logger.addHandler(self.mh)
        self.logger.addHandler(self.sh)

    def get_logger(self):
        return self.logger

    def debug(self, msg):
        if msg is not None:
            self.logger.debug(msg)

    def info(self, msg):
        if msg is not None:
            self.logger.info(msg)

    def warning(self, msg):
        if msg is not None:
            self.logger.warning(msg)

    def error(self, msg):
        if msg is not None:
            self.logger.error(msg)

    def critical(self, msg):
        if msg is not None:
            self.logger.critical(msg)

logger = Logger(LOG_FILE_PATH, FILE_LOG_LEVEL, CONSOLE_LOG_LEVEL, MEMORY_LOG_LEVEL, URGENT_LOG_LEVEL).get_logger()

if __name__ == "__main__":
    # 测试代码
    for i in range(50):
        logger.error(i)
        logger.debug(i)
    logger.critical("Database has gone away")
