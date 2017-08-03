#!/usr/bin/env python
# -*- coding: utf-8 -*-

import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
import logging

from ..configs import configs

__author__ = "East"
__created__ = "2017/3/18 18:52"

# 获取配置信息
log_configs = configs.get("log")
LOG_FILE_PATH = log_configs.get("log_file_path")

# 邮件服务器配置
MAIL_HOST = log_configs.get("mail_host")
MAIL_PORT = log_configs.get("mail_port")
USER = log_configs.get("user")
PASSWORD = log_configs.get("password")
FROM = log_configs.get("from")
MAIL_TO = log_configs.get("mail_to")

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


def send_mail(host: str, port: int, user: str, password: str,
              from_address: str, to_address: list or str, subject: str, content: str, ssl=True):
    """
        发送邮件的方法
    """
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = _format_addr('链科爬虫 <%s>' % from_address)
    msg['To'] = ";".join(to_address)
    mail_to = ";".join(to_address)
    try:
        if ssl:
            s = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            s = smtplib.SMTP(host, port, timeout=10)
        s.set_debuglevel(1)
        s.login(user=user, password=password)
        s.sendmail(from_address, mail_to, msg.as_string())
        s.close()
    except Exception as e:
        logger.error("邮件发送失败")
        logger.exception(e)


def send_mail2(subject: str, content: str):
    send_mail(MAIL_HOST, MAIL_PORT, USER, PASSWORD, FROM, MAIL_TO, subject, content)
    logger.info("邮件发送成功: 发件人: {from_address}, 收件人: {to_address}".format(
        from_address=FROM, to_address=MAIL_TO))


# def send_mail(host: str, port: int, user: str, password: str,
#               from_address: str, to_address: list or str, subject: str, content: str, ssl=True):
#     """
#         发送邮件的方法
#     """
#     msg = MIMEText(content)
#     msg['Subject'] = subject
#     msg['From'] = _format_addr('链科爬虫 <%s>' % from_address)
#     msg['To'] = ";".join(to_address)
#     mail_to = ";".join(to_address)
#     try:
#         if ssl:
#             s = smtplib.SMTP_SSL(host, port)
#         else:
#             s = smtplib.SMTP(host, port)
#         s.set_debuglevel(1)
#         s.login(user=user, password=password)
#         s.sendmail(from_address, mail_to, msg.as_string())
#         s.close()
#         logger.info("邮件发送成功: 发件人: {from_address}, 收件人: {to_address}".format(
#             from_address=from_address, to_address=to_address))
#     except Exception as e:
#         logger.exception(e)
#         logger.error("邮件发送失败")

if __name__ == '__main__':
    send_mail("smtp.qq.com", 465, "1078828995@qq.com", "ahawvcullwtljcfh", "1078828995@qq.com",
              ["dongfang4021@163.com", "1074518411@qq.com"], "z这是一封测试邮件", "hello")
