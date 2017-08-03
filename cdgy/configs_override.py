#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "dong fang"

configs = {
    "log": {
        "log_file_path": "spider_log/spider.log",
        "file_log_level": "DEBUG",  # 写入文件的日志等级，由于是详细信息，推荐设为debug
        "console_log_level": "DEBUG",  # 控制台的日照等级，info和warning都可以，可以按实际要求定制
        "memory_log_level": "ERROR",  # 缓存日志等级，最好设为error或者critical
        "urgent_log_level": "CRITICAL",  # 致命错误等级
        # 缓存溢出后的邮件标题
        "error_threshold_achieved_mail_subject": "爬虫运行过程中的错误数量超过50个",
        "error_message_threshold": 50,  # 缓存溢出的阀值
        # 致命错误发生后的邮件标题
        "critical_error_achieved_mail_subject": "爬虫崩溃，请及时检查爬虫的运行状态",
        "mail_host": "smtp.qq.com",  # 邮件服务器
        "mail_port": 465,  # 邮件服务器端口
        "user": "1074518411@qq.com",  # 邮箱用户名
        "password": ".lyF4021125@mdF",  # 邮箱密码
        "from": "1074518411@qq.com",  # 发件人， 最好与用户名相同，否则邮件服务商可能退信
        "mail_to": ["dongfang4021@163.com", "1074518411@qq.com"]  # 收件人
    },
    "db": {
        "host": "112.74.45.98",
        "port": "3306",
        "user": "root",
        "password": "1234"
    },
}
