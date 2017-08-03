#!/usr/bin/env python
# -*- coding: utf-8 -*-


import random

from .config_util import CONFIG_USERAGENT_PC

__author__ = "dong fang"


def random_choice_ua():
    return random.choice(CONFIG_USERAGENT_PC)
