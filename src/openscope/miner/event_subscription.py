#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/28 19:41
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : event_subscription.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :
import argparse
import asyncio
import sys
from os.path import dirname, realpath

import requests
import websockets
from fastapi import HTTPException
from retrying import retry

sys.path.append(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}')

from src.openscope.utils import log


async def subscription_realtime():
    log('subscription_realtime begin')
    url = "ws://47.236.87.93:8000/ws/getevents"
    async with websockets.connect(url) as websocket:
        response = await websocket.recv()  # Receive server response
        if response:
            log("Received message from server:", response)
        else:
            log("No message received from server")


@retry(wait_fixed=5000, stop_max_attempt_number=2)
def subscription_history():
    log('subscription_history begin')
    url = "http://47.236.87.93:8000/getallevents"
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    if response.json().get('code') != 200:
        raise HTTPException(status_code=response.json().get('code'), detail=response.json().get('msg'))
    log(response.text)
    return response.json()


def main(history_flag):
    if history_flag:
        subscription_history()
    else:
        asyncio.run(subscription_realtime())
    log('event_subscription end')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="subscription event")
    parser.add_argument("-history", action="store_true", help="subscription history event or realtime event by ws")
    args = parser.parse_args()
    main(args.history)
