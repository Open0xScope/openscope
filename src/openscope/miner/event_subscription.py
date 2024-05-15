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
import os.path
import sys
import time
from os.path import dirname, realpath

import pandas as pd
import requests
from fastapi import HTTPException
from retrying import retry

sys.path.append(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}')

from src.openscope.utils import log


def subscription_realtime(begin_time):
    log('subscription_realtime begin')
    while True:
        end_time = int(time.time())
        get_events(begin_time, end_time)
        begin_time = end_time + 1
        log(f'Wait {WAIT_TIME}s for the next round to fetch data after one round ends. ')
        time.sleep(WAIT_TIME)


@retry(wait_fixed=5000, stop_max_attempt_number=2)
def get_events(begin_time=None, end_time=None):
    url = "http://47.236.87.93:8000/getallevents"
    headers = {
        'Content-Type': 'application/json'
    }

    params = dict()
    if begin_time is not None:
        params['start'] = begin_time
    if end_time is not None:
        params['end'] = end_time

    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    if response.json().get('code') != 200:
        raise HTTPException(status_code=response.json().get('code'), detail=response.json().get('msg'))
    return response.json()


def subscription_history():
    log('subscription_history begin')
    data = get_events()
    historic_events_file = os.path.join(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}',
                                        'resources/historic_events.csv ')
    if data.get('data'):
        df = pd.DataFrame(data.get('data'))
        df.to_csv(historic_events_file, index=False, header=True)
        log(f'History events successfully saved under {historic_events_file}')
    log('subscription_history end')


def main(history_flag, begin_time):
    if history_flag:
        subscription_history()
    else:
        subscription_realtime(begin_time)
    log('event_subscription end')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="subscription event")
    parser.add_argument("-history", action="store_true", help="subscription history event or realtime event by polling")
    parser.add_argument("-begin_time", type=int, default=int(time.time()) - 60, help="begin block_id add num")
    parser.add_argument("-wait_time", type=int, default=300, help="The polling wait time")
    args = parser.parse_args()
    WAIT_TIME = args.wait_time
    main(args.history, args.begin_time)
