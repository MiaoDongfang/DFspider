#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard Library


# Third-Party Library

# My Library
try:
    from cdgy import configs_override
except ImportError:
    settings = None
from .. import configs_default

__author__ = "dong fang"


def settings_to_dict(settings_module):
    """Return the default settings as an iterator of (name, value) tuples"""
    settings_dict = {}
    for name in dir(settings_module):
        if name.isupper():
            settings_dict[name] = getattr(settings_module, name)
    return settings_dict


def merge_dict(dict1, dict2):
    dict_fin = dict1
    for k, v in list(dict2.items()):
            dict_fin[k] = v
    return dict_fin


def merge_settings():
    dict1 = settings_to_dict(configs_default)
    dict2 = settings_to_dict(configs_override)
    return merge_dict(dict1, dict2)

spider_settings = merge_settings()

if __name__ == '__main__':
    pass
