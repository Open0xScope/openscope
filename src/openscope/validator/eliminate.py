#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/7/1 20:33
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : eliminate.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :
import json
import math
import os
import time
from datetime import datetime, timezone
from os.path import dirname, realpath

import pandas as pd
import sr25519
from communex.compat.key import classic_load_key
from trade import get_miner_registertime, get_recent_orders


def get_miners(keypair, timestamp, starttime=0):
    val_ss58 = keypair.ss58_address
    pub_key = keypair.public_key.hex()
    msg = f'{val_ss58}{pub_key}{timestamp}'.encode()
    signature = sr25519.sign((keypair.public_key, keypair.private_key), msg).hex()  # type: ignore
    result = get_miner_registertime(val_ss58, pub_key, timestamp, signature, starttime)
    return result


def get_orders(keypair, timestamp, tradetime=0):
    val_ss58 = keypair.ss58_address
    pub_key = keypair.public_key.hex()
    msg = f'{val_ss58}{pub_key}{timestamp}'.encode()
    signature = sr25519.sign((keypair.public_key, keypair.private_key), msg).hex()  # type: ignore
    orders = get_recent_orders(val_ss58, pub_key, timestamp, signature, tradetime)
    result = list()
    for order in orders:
        result.append(order.__dict__)
    return result


def not_active_elimination(keypair):
    '''Screen miners that have just passed the protection period and are inactive during the protection period.'''
    result = list()
    timestamp = int(time.time())
    timestamp_day = timestamp // 86400 * 86400
    tradetime = timestamp_day - 8 * 86400
    starttime = timestamp_day - 8 * 86400
    orders = get_orders(keypair, timestamp, tradetime)
    if not orders:
        return result
    all_miner = get_miners(keypair, timestamp, starttime)
    check_time_begin = timestamp_day - 8 * 86400
    check_time_end = timestamp_day - 7 * 86400 - 1

    miner_expired = [{'address': address, 'register_time': register_time, 'expired_time': register_time + 7 * 86400} for
                     address, register_time in all_miner.items() if
                     (register_time >= check_time_begin) and (register_time <= check_time_end)]
    if not miner_expired:
        return result
    df_miner = pd.DataFrame(miner_expired)
    df = pd.DataFrame(orders)
    merged_df = df.merge(df_miner, left_on='MinerId', right_on='address')
    filtered_df = merged_df[
        (merged_df['TimeStamp'] >= merged_df['register_time']) & (merged_df['TimeStamp'] <= merged_df['expired_time'])]
    filtered_df = filtered_df.groupby('MinerId').filter(
        lambda x: len(x) > 3 and (x['isClose'] == False).sum() >= 2).reset_index(
        drop=True)
    result = list(set(df_miner['address'].unique()) - set(filtered_df['MinerId'].unique()))

    return list(result)


def ceil_to_integer(num):
    return math.ceil(num)


def check_copy_trading(df_1, df_2):
    check_rate = 0.95
    row_num = len(df_1)
    copy_num = 0
    no_copy_num = 0
    check_copy_num = ceil_to_integer(row_num * check_rate)
    check_no_copy_num = ceil_to_integer(row_num * (1 - check_rate - 0.000001))
    for index, row in df_1.iterrows():
        token = row.Token
        close = row.isClose
        direction = row.Direction
        timestamp = row.TimeStamp
        leverage = row.Leverage
        b_timestamp = timestamp - 30

        filtered_df = df_2[
            (df_2['Token'] == token) &
            (df_2['Direction'] == direction) &
            (df_2['Leverage'] == leverage) &
            (df_2['isClose'] == close) &
            (df_2['TimeStamp'] < timestamp) &
            (df_2['TimeStamp'] >= b_timestamp)
            ]
        if filtered_df.empty:
            no_copy_num += 1
        else:
            copy_num += 1
        if copy_num >= check_copy_num:
            return True
        elif no_copy_num >= check_no_copy_num:
            return False
        else:
            continue
    else:
        raise Exception(f'check_copy_trading func error')


def copy_trading_elimination(keypair) -> dict:
    result = dict()
    timestamp = int(time.time())
    tradetime = timestamp - 7 * 86400
    orders = get_orders(keypair, timestamp, tradetime)
    df = pd.DataFrame(orders)
    if df.empty:
        return result
    all_miner = list(df['MinerId'].unique())
    for t1_miner in all_miner:
        for t2_miner in all_miner:
            if t1_miner == t2_miner:
                continue
            df_1 = df[df['MinerId'] == t1_miner]
            df_2 = df[df['MinerId'] == t2_miner]
            if df_1.shape[0] < 5 or df_2.shape[0] < 5:
                continue
            if check_copy_trading(df_1, df_2):
                # print(t1_miner, t2_miner)
                result[t1_miner] = t2_miner
    return result


def filter_groups_roi_elimination(group):
    consecutive_count = 0
    total_count = 0
    for roi in group['roi']:
        if roi < -50:
            consecutive_count += 1
            total_count += 1
            if consecutive_count >= 2 or total_count >= 5:
                return True
        else:
            consecutive_count = 0
    return False


def roi_elimination(checkpoints) -> list:
    data = list()
    for value in checkpoints:
        last_update = value.last_update
        rois = value.roi
        if not last_update or not rois:
            continue
        formatted_date = datetime.fromtimestamp(last_update, tz=timezone.utc).strftime('%Y-%m-%d')
        for address, roi in rois.items():
            tmp_data = dict()
            tmp_data['address'] = address
            tmp_data['last_update'] = last_update
            tmp_data['last_update_day'] = formatted_date
            tmp_data['roi'] = roi
            data.append(tmp_data)
    current_time = int(time.time()) // 86400 * 86400
    check_time = current_time - 30 * 86400
    # columns = ['address', 'last_update', 'last_update_day', 'roi']
    df = pd.DataFrame(data)
    if df.empty:
        return []
    filtered_df = df[df['last_update'] >= check_time]
    filtered_df = filtered_df.sort_values(by='last_update', ascending=False).groupby(
        ['address', 'last_update_day']).first().reset_index()
    filtered_result = filtered_df.groupby('address').filter(filter_groups_roi_elimination)
    unique_miner_ids = list(filtered_result['address'].unique())
    return unique_miner_ids


def mdd_elimination(mdd_data) -> list:
    unique_miner_ids = [key for key, value in mdd_data.items() if value < -0.5]
    return unique_miner_ids


def get_protected_miner(keypair) -> list:
    timestamp = int(time.time())
    starttime = timestamp - 7 * 86400
    protect_miner = get_miners(keypair, timestamp, starttime)
    return list(protect_miner.keys())


def save_eliminate_data(eliminate_data, file=None):
    if not file:
        file = os.path.join(dirname(realpath(__file__)), 'eliminate.json')
    data = {key: value for key, value in eliminate_data.items() if value['status']}
    with open(file, 'w') as fd:
        fd.write(json.dumps(data))


def get_eliminate_data(file=None):
    result = dict()
    if not file:
        file = os.path.join(dirname(realpath(__file__)), 'eliminate.json')
    if not os.path.exists(file):
        return result
    if (int(time.time()) - int(os.path.getmtime(file))) > 7 * 86400:
        return result
    with open(file, 'r') as fd:
        data = fd.read() or '{}'
        result = json.loads(data)
    return result


def main():
    keypair = classic_load_key('validator_11')
    # print(not_active_elimination(keypair))
    # print(get_protected_miner(keypair))
    # print(get_eliminate_data())
    # print(copy_trading_elimination(keypair))
    # save_eliminate_data({'a':True,'b':False})
    print(roi_elimination([]))


if __name__ == '__main__':
    main()
