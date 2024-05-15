#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 18:06
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : _config.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :

import configparser

# config = configparser.ConfigParser()
# config.read("config.ini")


class Config:
    def __init__(self, config_file):
        if config_file is None:
            config_file = '../../../env/config.ini'
        config = configparser.ConfigParser()
        config.read(config_file)
        self.miner = {
            "keyfile": config.get("miner", "keyfile"),
            "url": config.get("miner", "url"),
        }
        self.api = {
            "url": config.get("api", "url"),
        }
