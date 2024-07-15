#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 18:04
# @Author  : long.zhang
# @Contact : long.zhang@opg.global
# @Site    : scope
# @File    : signal_trade.py
# @Software: PyCharm
# @Desc    :
# @Cmd     :
import argparse
import json
import os
import sys
import re
import time
from abc import ABC
from os.path import dirname, realpath
from urllib.parse import urljoin, urlparse

import requests
import uvicorn
from communex.compat.key import classic_load_key
from communex.module.module import Module, endpoint  # type: ignore
from communex.module.server import ModuleServer  # type: ignore
from communex.module._rate_limiters.limiters import IpLimiterParams
from fastapi import HTTPException
from loguru import logger

sys.path.append(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}')
from json.decoder import JSONDecodeError

from config import Config
from requests.exceptions import HTTPError
from src.openscope.key import sign_message
from src.openscope.utils import is_ethereum_address


class TradeModule(ABC, Module):

    def __init__(self, server_url: str) -> None:
        """
        Initialize the TradeModule with the server URL.

        Args:
            server_url (str): The base URL of the server.
        """
        super().__init__()
        self.trade_url = urljoin(server_url, 'createtrade')
        self.user_trades_url = urljoin(server_url, 'getusertrades')

    @staticmethod
    def _validate_required_params(data: dict, required_params: list[str]) -> None:
        missing_params = [param for param in required_params if param not in data]
        if missing_params:
            raise HTTPException(status_code=400, detail=f"Missing required parameters: {missing_params}")

    @staticmethod
    def _is_valid_leverage(input_str: str | int | float) -> bool:
        try:
            number = float(input_str)
            if 0.1 <= number <= 20 and re.match(r"^\d+(\.\d{1})?$", str(input_str)):
                return True
        except ValueError:
            pass
        return False

    @endpoint
    def trade(self, data: dict):
        try:
            logger.info(f'data: {data}')
            self._validate_required_params(data, ['token', 'position_manager', 'direction'])
            miner_id = os.getenv('SIGNAL_TRADE_ADDRESS')
            pub_key = os.getenv('SIGNAL_TRADE_PUBLIC_KEY')
            nonce = int(time.time() * 1000)
            token = data['token'].lower()
            if not is_ethereum_address(token):
                raise HTTPException(status_code=400, detail=f"The token: {token} is an invalid EVM address")

            leverage = data.get('leverage', 0.1)
            if not self._is_valid_leverage(leverage):
                raise HTTPException(status_code=400,
                                    detail=f"leverage: {leverage} is an invalid leverage, Need a float value between 0.1 and 20, inclusive, with a precision of 0.1.Examples of valid values: 0.1, 0.2, 1.0, 5.5, 19.9, 20.0.")
            leverage = int(leverage) if int(leverage) == leverage else float(leverage)
            position_manager = data['position_manager']
            direction = int(data['direction'])
            timestamp = nonce // 1000

            trade_data = {'miner_id': miner_id, 'pub_key': pub_key, 'nonce': nonce, 'token': token,
                          'position_manager': position_manager, 'direction': direction, 'timestamp': timestamp,
                          'leverage': leverage}

            sing_msg = f'{miner_id}{pub_key}{nonce}{token}{position_manager}{direction}{timestamp}{leverage}'
            signature = sign_message(os.getenv('SIGNAL_TRADE_PRIVATE_KEY'), sing_msg)
            trade_data['signature'] = signature
            logger.info(f'trade_data: {trade_data}')
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.post(
                url=self.trade_url,
                headers=headers,
                data=json.dumps(trade_data)
            )
            logger.info(response.text)
            response.raise_for_status()
            if response.json().get('code') != 200:
                raise HTTPException(status_code=response.json().get('code'), detail=response.json().get('msg'))
        except HTTPError as http_err:
            raise HTTPException(status_code=http_err.response.status_code, detail=str(http_err)) from http_err
        except JSONDecodeError as json_err:
            raise HTTPException(status_code=500, detail="Failed to decode JSON response") from json_err
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred") from e

    @endpoint
    def user_trades(self):
        try:
            miner_id = os.getenv('SIGNAL_TRADE_ADDRESS')
            pub_key = os.getenv('SIGNAL_TRADE_PUBLIC_KEY')
            timestamp = int(time.time())
            sing_msg = f'{miner_id}{pub_key}{timestamp}'
            signature = sign_message(os.getenv('SIGNAL_TRADE_PRIVATE_KEY'), sing_msg)
            params = {'userId': miner_id, 'pubKey': pub_key, 'timestamp': timestamp, 'sig': signature}
            response = requests.get(url=self.user_trades_url, params=params)
            response.raise_for_status()
            if response.json().get('code') != 200:
                raise HTTPException(status_code=response.json().get('code'), detail=response.json().get('msg'))
            return response.json()['data']
        except HTTPError as http_err:
            raise HTTPException(status_code=http_err.response.status_code, detail=str(http_err)) from http_err
        except JSONDecodeError as json_err:
            raise HTTPException(status_code=500, detail="Failed to decode JSON response") from json_err
        except Exception as e:
            raise HTTPException(status_code=500, detail="An unexpected error occurred") from e


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Assemble and send trade")
    parser.add_argument("-config_file", type=str,
                        default=os.path.join(f'{dirname(dirname(dirname(dirname(realpath(__file__)))))}',
                                             'env/config.ini'), help=f"config file path")
    args = parser.parse_args()
    config_file = args.config_file
    config = Config(config_file=config_file)
    logger.add(f"{dirname(realpath(__file__))}/logs/signal_trade_{config.miner.get('keyfile')}_{{time:YYYY-MM-DD}}.log",
               rotation="1 day")
    keypair = classic_load_key(config.miner.get("keyfile"))
    url = config.miner.get("url")
    parsed_url = urlparse(url)
    logger.info(f"Running module with key {keypair.ss58_address}")
    os.environ["SIGNAL_TRADE_ADDRESS"] = keypair.ss58_address
    os.environ["SIGNAL_TRADE_PUBLIC_KEY"] = keypair.public_key.hex()
    os.environ["SIGNAL_TRADE_PRIVATE_KEY"] = keypair.private_key.hex()
    server_url = config.api.get("url")
    claude = TradeModule(server_url)

    server = ModuleServer(
        claude, keypair, limiter=IpLimiterParams(), subnets_whitelist=[3]
    )
    app = server.get_fastapi_app()
    app.add_api_route("/trade", claude.trade, methods=["POST"])
    app.add_api_route("/user_trades", claude.user_trades, methods=["GET"])
    uvicorn.run(app, host=parsed_url.hostname, port=parsed_url.port)
