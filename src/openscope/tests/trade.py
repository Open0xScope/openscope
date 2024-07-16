#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/29 11:38
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : trade.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :

import requests


def main():
    url = "http://127.0.0.1:5000/trade"
    data = {
        "token": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "position_manager": "open",
        "direction": -1,
        "leverage": 0.1
    }

    response = requests.post(url, json=data)

    print(response.status_code)
    print(response.json())


if __name__ == '__main__':
    main()
