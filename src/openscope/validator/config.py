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


class Config:
    def __init__(self, config_file):
        if config_file is None:
            config_file = 'env/config.ini'        
        config = configparser.ConfigParser()
        config.read(config_file)
        user = config.get("database", "user")
        password = config.get("database", "password")
        host = config.get("database", "host")
        port =  config.get("database", "port")
        name = config.get("database", "name")
        self.database = {
            "uri": f'postgresql://'+user+':'+password+'@'+host+':'+port+'/'+name+'?sslmode=disable'
        }
        self.validator = {
            "name": config.get("validator","name"),
            "keyfile": config.get("validator", "keyfile"),
            "interval": config.get("validator", "interval"),
        }
        self.api = {
            "url": config.get("api","url"),
        }
