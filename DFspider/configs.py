#!/usr/bin/env python
# -*- coding: utf-8 -*-

from . import configs_default


def merge_dict(defaults, override):
    r = override
    for k, v in defaults.items():
        if k in override:
            if isinstance(v, dict):
                r[k] = merge_dict(v, override[k])
            else:
                r[k] = override[k]
        else:
            r[k] = v
    return r

configs = configs_default.configs

try:
    from . import configs_override
    configs = merge_dict(configs, configs_override.configs)
except ImportError:
    pass
