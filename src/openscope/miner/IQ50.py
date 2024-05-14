#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/13 10:55
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : IQ50.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :
import argparse
import json
import os
import random
import sys
import time
from os.path import dirname, realpath
from urllib.parse import urlparse

import pandas as pd
import requests
from communex.compat.key import classic_load_key
from communex.module.module import Module, endpoint  # type: ignore
from communex.module.server import ModuleServer  # type: ignore
from loguru import logger
from retrying import retry

sys.path.append(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}')
from config import Config

DEFAULT_TOKENS = ["0x514910771af9ca656af840dff83e8264ecf986ca", "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
                  "0x6982508145454ce325ddbe47a25d4ec3d2311933", "0xaea46a60368a7bd060eec7df8cba43b7ef41ad85",
                  "0x808507121b80c02388fad14726482e061b8da827", "0x9d65ff81a3c488d585bbfb0bfe3c7707c7917f54",
                  "0x6e2a43be0b1d33b726f0ca3b8de60b3482b8b050", "0xc18360217d8f7ab5e7c516566761ea12ce7f9d72",
                  "0xa9b1eb5908cfc3cdf91f9b8b3a74108598009096", "0x57e114b691db790c35207b2e685d4a43181e6061"]


@retry(wait_fixed=5000, stop_max_attempt_number=2)
def get_user_trades():
    response = requests.get(USER_TRADES_URL)
    if response.status_code != 200:
        raise Exception(
            f'get_user_trades: error,response.status_code: {response.status_code}, response.text: {response.text}')
    return response.json()


def get_user_latest_trades() -> dict:
    '''
    Retrieve the latest orders at the user token level.
    Returns:

    '''
    data = get_user_trades()
    result = dict()
    if data:
        df = pd.DataFrame(data, columns=['TokenAddress', 'PositionManager', 'Direction', 'Timestamp'])
        df_sorted = df.sort_values(by='Timestamp', ascending=False)
        # Group by TokenAddress and take the first record of each group.
        df_sorted_first = df_sorted.groupby('TokenAddress', as_index=False).first()
        result_list = df_sorted_first[['TokenAddress', 'PositionManager', 'Direction']].to_dict(orient='records')
        for data in result_list:
            result[data['TokenAddress']] = data
    return result


def get_random_direction():
    return random.choice([1, -1])


def get_strategy_trades(latest_trades) -> list:
    random_tokens = random.sample(DEFAULT_TOKENS, 3)
    result = list()
    for token in random_tokens:
        tmp_trades = list()
        if token not in latest_trades or latest_trades[token]['PositionManager'] == 'close':
            tmp_trades.append({
                "token": token,
                "position_manager": "open",
                "direction": get_random_direction()
            })
        else:
            # latest_trades[token]['position_manager'] == 'open'
            tmp_trades.append({
                "token": token,
                "position_manager": "close",
                "direction": latest_trades[token]['Direction']
            })
            direction = get_random_direction()
            if direction != latest_trades[token]['Direction']:
                tmp_trades.append({
                    "token": token,
                    "position_manager": "open",
                    "direction": direction
                })
        result.append(tmp_trades)
    logger.info(json.dumps(result))
    return result


@retry(wait_fixed=5000, stop_max_attempt_number=2)
def send_trade(trade):
    logger.info(f'send_trade begin: {trade}')
    response = requests.post(SIGNAL_TRADE_URL, json=trade)
    if response.status_code != 200:
        raise Exception(
            f'send_trade: error,response.status_code: {response.status_code}, response.text: {response.text}')


def send_trades(trades):
    try:
        for trade in trades:
            send_trade(trade)
            time.sleep(random.randint(5, 10))
    except Exception as e:
        logger.error(f'trades: {trades} error, e:{e}')


def send_trades_all(all_trades):
    for trades in all_trades:
        send_trades(trades)


def main():
    latest_trades = get_user_latest_trades()
    logger.info(f'latest_trades: {latest_trades}')
    strategy_trades = get_strategy_trades(latest_trades)
    send_trades_all(strategy_trades)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="IQ 50 miner")
    parser.add_argument("-config_file", type=str,
                        default=os.path.join(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}',
                                             'env/config.ini'), help=f"config file path")
    args = parser.parse_args()
    config_file = args.config_file
    config = Config(config_file=config_file)
    logger.add(f"{dirname(realpath(__file__))}/logs/IQ50_{config.miner.get('keyfile')}_{{time:YYYY-MM-DD}}.log",
               rotation="1 day")
    keypair = classic_load_key(config.miner.get("keyfile"))
    url = config.miner.get("url")
    parsed_url = urlparse(url)
    SIGNAL_TRADE_URL = f'http://{parsed_url.hostname}:{parsed_url.port}/trade'
    USER_TRADES_URL = f'http://{parsed_url.hostname}:{parsed_url.port}/user_trades'
    logger.info(f"Running IQ 50 module with key {keypair.ss58_address}")
    os.environ["SIGNAL_TRADE_ADDRESS"] = keypair.ss58_address
    os.environ["SIGNAL_TRADE_PUBLIC_KEY"] = keypair.public_key.hex()
    os.environ["SIGNAL_TRADE_PRIVATE_KEY"] = keypair.private_key.hex()
    main()
