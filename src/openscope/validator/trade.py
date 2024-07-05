from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Union
import requests
from dateutil.tz import UTC
import sr25519
from substrateinterface import Keypair 
from config import Config
from storage import LocalStorage

DEFAULT_TOKENS = ['0xc011a73ee8576fb46f5e1c5751ca3b9fe0af2a6f', '0xfaba6f8e4a5e8ab82f62fe7c39859fa577269be3',
                  '0x4d224452801aced8b2f0aebe155379bb5d594381', '0x5283d291dbcf85356a21ba090e6db59121208b44',
                  '0x5a98fcbea516cf06857215779fd812ca3bef1b32', '0x4200000000000000000000000000000000000042',
                  '0x912ce59144191c1204e64559fe8253a0e49e6548', '0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9',
                  '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599', '0x0000000000000000000000000000000000000000',
                  '0x57e114b691db790c35207b2e685d4a43181e6061', '0xa9b1eb5908cfc3cdf91f9b8b3a74108598009096',
                  '0xc18360217d8f7ab5e7c516566761ea12ce7f9d72', '0x6e2a43be0b1d33b726f0ca3b8de60b3482b8b050',
                  '0x9d65ff81a3c488d585bbfb0bfe3c7707c7917f54', '0x808507121b80c02388fad14726482e061b8da827',
                  '0xaea46a60368a7bd060eec7df8cba43b7ef41ad85', '0x6982508145454ce325ddbe47a25d4ec3d2311933',
                  '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984', '0x514910771af9ca656af840dff83e8264ecf986ca']

MAIN_TOKENS = ['0x0000000000000000000000000000000000000000', '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599']


class Account:
    def __init__(self, Portfolio={}, AvgPrice=None, WinRate=None, TokenRate=None, Leverage=None, Balance=10,
                 TimeStamp=0):
        self.Portfolio = Portfolio
        self.InitialBalance = Balance
        self.Profit = 0.0
        self.AvgPrice = {} if AvgPrice is None else AvgPrice.copy()
        self.FirstTrade = TimeStamp
        self.WinRate = {} if WinRate is None else WinRate.copy()
        self.TokenRate = {} if TokenRate is None else TokenRate.copy()
        self.Leverage = {} if Leverage is None else Leverage.copy()

    def update_balance(self, profit: float):
        self.Profit += profit
        for asset, value in self.Portfolio.items():
            if value.get("asset", 0.0) == 0:
                new_asset = {
                    "usd": self.Profit + self.InitialBalance,
                    "asset": 0.0
                }
                self.Portfolio[asset] = new_asset
        return
            
def init_account():
    portfolio = {}
    for item in DEFAULT_TOKENS:
        asset = {
            "asset": 0.0,
            "usd": 10.0
        }
        portfolio[item] = asset
    account = Account(portfolio)
    return account


class Order:
    def __init__(self, MinerId="", Token="", isClose=False, Direction=0, Nonce=0, Price=0, Price4H=0, TimeStamp=0,
                 Leverage=1):
        self.MinerId = MinerId
        self.Token = Token
        self.isClose = isClose
        self.Direction = Direction
        self.Nonce = Nonce
        self.Price = Price
        self.Price4H = Price4H
        self.TimeStamp = TimeStamp
        self.Leverage = Leverage

class PositionCheckpoint:
    def __init__(self, last_update: int, cur_ret: Dict[str, float] = None, prev_ret: Dict[str, float] = None, roi: Dict[str, float] = None, orders: List[Order] = []):
        self.last_update = last_update
        self.cur_ret = {} if cur_ret is None else cur_ret.copy()
        self.prev_ret = {} if prev_ret is None else prev_ret.copy()
        self.roi = {} if roi is None else roi.copy()
        self.orders = orders
        self.is_update = False
        
class AccountManager(LocalStorage):
    def __init__(self, config=None, logger=None):
        super().__init__(config=config, logger=logger)
        self.checkpoints = []
    
    def group_orders_by_day(self, orders: List[Order]) -> None:
        for order in orders:
            timestamp = order.TimeStamp
            utc_datetime = datetime.fromtimestamp(timestamp, tz=UTC)
            date = utc_datetime.date()
            matching_checkpoint = next((checkpoint for checkpoint in self.checkpoints 
                                        if datetime.fromtimestamp(checkpoint.last_update, tz=UTC).date() == date), None)
            if matching_checkpoint:
                matching_checkpoint.orders.append(order)
            else:
                last_update = int(datetime.combine(date, datetime.min.time(), tzinfo=UTC).timestamp())
                current_checkpoint = PositionCheckpoint(last_update=last_update, orders=[order])
                self.checkpoints.append(current_checkpoint)
        
        self.checkpoints = sorted(self.checkpoints, key=lambda checkpoint: checkpoint.last_update)
        return

    def process_orders_by_day(self, latest_price: Dict[str, float], addr: str, pub_key: str, keypair: Keypair):
        if len(self.checkpoints) == 0:
            return {}, {}, {}
        
        if len(self.checkpoints) > 1:
            for i in range(len(self.checkpoints) - 1):
                checkpoint = self.checkpoints[i]
                if checkpoint.is_update:
                    continue
                timestamp = int(time.time())
                msg = f'{addr}{pub_key}{timestamp}'
                message = format_data(msg)
                signature = sr25519.sign(  # type: ignore
                    (keypair.public_key, keypair.private_key), message).hex()
                # max_timestamp = max(checkpoint.orders, key=lambda order: order.TimeStamp).TimeStamp
                max_timestamp = checkpoint.last_update + 24*3600
                current_price = get_latest_price(addr, pub_key, timestamp, signature, max_timestamp)
                if len(current_price.keys()) != len(DEFAULT_TOKENS):
                    self.logger.error(f'get token price error')
                for order in checkpoint.orders:
                    self.process_order(order, current_price)

                for id, account in self.accounts.items():
                    if account.FirstTrade > 0:
                        formatted_time = datetime.fromtimestamp(float(checkpoint.last_update)).strftime('%Y-%m-%d %H:%M:%S')
                        roi, _, _ = evaluate_account(account, current_price)
                        position_value = roi * account.InitialBalance / 100 + account.InitialBalance
                        checkpoint.cur_ret[id] = position_value
                        checkpoint.roi[id] = roi
                        if i == 0:
                            checkpoint.prev_ret[id] = 10.0
                        else:
                            prev_point = self.checkpoints[i-1]
                            checkpoint.prev_ret[id] = prev_point.cur_ret.get(id, 10.0)
                        self.logger.info(f"{id} position_value: {position_value}, time: {formatted_time}")
                checkpoint.is_update = True
        
        # handle last checkpoint
        checkpoint = self.checkpoints[-1]
        roi_data = {}
        win_data = {}
        position_data = {}
        for order in checkpoint.orders:
            self.process_order(order, latest_price)
        for id, account in self.accounts.items():
            if account.FirstTrade > 0:
                roi, win_rate, position = evaluate_account(account, latest_price)
                position_value = roi * account.InitialBalance / 100 + account.InitialBalance
                roi_data[id] = roi
                win_data[id] = win_rate
                position_data[id] = position
                checkpoint.cur_ret[id] = position_value
                checkpoint.roi[id] = roi
                if len(self.checkpoints) == 1:
                    checkpoint.prev_ret[id] = 10.0
                else:
                    prev_point = self.checkpoints[-2]
                    checkpoint.prev_ret[id] = prev_point.cur_ret.get(id, 10.0)
                self.logger.info(f"{id} roi data: {roi}, latest position_value: {position_value}")
        checkpoint.is_update = True
        
        # delete old checkpoint
        one_month_ago = datetime.now(tz=UTC) - timedelta(days=30)
        one_month_ago_timestamp = int(one_month_ago.timestamp())

        self.checkpoints = [checkpoint for checkpoint in self.checkpoints 
                           if checkpoint.last_update >= one_month_ago_timestamp]
        #write to disk
        return roi_data, win_data, position_data
    
    def generate_returns(self) -> Dict[str, List[float]]:
        result = {}
        for checkpoint in self.checkpoints:
            for id in checkpoint.cur_ret.keys():
                if id not in result:
                    result[id] = []
                return_change = (checkpoint.cur_ret[id] - checkpoint.prev_ret.get(id, 10.0)) / checkpoint.prev_ret.get(id, 10.0)
                result[id].append(return_change)
        return result
    
    def process_order(self, order: Order, latest_price: Dict[str, float]):
        address = order.MinerId
        token = order.Token
        # test
        # if address != '5D7EAkqrTcwWwJkZj4aQMqoKZSuk9sUYn881QTtGPFVfdsrP':
        #     return
        
        # validate miner
        if address not in self.accounts.keys():
            return
        account = self.accounts.get(address)
        if account.FirstTrade == 0 or account.FirstTrade > order.TimeStamp:
            account.FirstTrade = order.TimeStamp
        # calculate winrate, only calculate open order
        if not order.isClose:
            if order.Price4H == 0:
                order.Price4H = latest_price.get(token, 0)
            account.TokenRate[order.Nonce] = order.Token
            if order.Price < order.Price4H and order.Direction == 1:
                account.WinRate[order.Nonce] = 1
            elif order.Price > order.Price4H and order.Direction == -1:
                account.WinRate[order.Nonce] = 1
            else:
                account.WinRate[order.Nonce] = 0

        # tranfer_fee
        if token in MAIN_TOKENS:
            fee = 0.05 / 100
        else:
            fee = 0.1 / 100 * order.Leverage

        # calculate portfolio
        asset = account.Portfolio.get(token, {})
        if order.isClose:
            new_asset = {
                "asset" : 0.0,
            }
            balance = asset.get("asset", 0)
            avg_price = account.AvgPrice.get(token, 0)
            leverage = account.Leverage.get(token, 1)
            cost = 0
            if avg_price == 0:
                return
            if balance > 0 :
                # usd = balance * order.Price
                usd = balance * avg_price  * (1 + leverage * (order.Price-avg_price)/avg_price)
                cost = balance * avg_price 
            else:
                usd = (-balance) * avg_price  * (1 - leverage * (order.Price-avg_price)/avg_price)
                cost = (-balance) * avg_price
            new_asset["usd"] = usd
            account.Portfolio[token] = new_asset
            account.AvgPrice[token] = 0
            account.Leverage[token] = 1
            account.update_balance(usd - cost)
        else:
            if order.Direction == 1:
                usd_balance = asset.get("usd", 0)
                if usd_balance > 0:  
                    new_asset = {
                        "usd" : 0.0,
                        "asset": usd_balance * (1 - fee) / order.Price 
                    }
                    account.Portfolio[token] = new_asset
                    account.AvgPrice[token] = order.Price
                    account.Leverage[token] = order.Leverage
                else:
                    token_balance = asset.get("asset", 0)
                    if token_balance < 0:
                        avg_price = account.AvgPrice.get(token, 0)
                        leverage = account.Leverage.get(token, 1)
                        if avg_price == 0:
                            return
                        usd = (-token_balance) * avg_price  * (1 - leverage * (order.Price-avg_price)/avg_price)
                        amount = usd  * (1 - fee) / order.Price
                        new_asset = {
                            "asset": amount,
                            "usd": 0.0,
                        }
                        account.Portfolio[token] = new_asset
                        account.AvgPrice[token] = order.Price
                        account.Leverage[token] = order.Leverage
            else:
                usd_balance = asset.get("usd", 0)
                if usd_balance > 0:  
                    new_asset = {
                        "usd" : 0.0,
                        "asset": usd_balance  * (1 - fee) / order.Price * (-1)
                    }
                    account.Portfolio[token] = new_asset
                    account.AvgPrice[token] = order.Price
                    account.Leverage[token] = order.Leverage
                else:
                    token_balance = asset.get("asset", 0)
                    if token_balance > 0:
                        avg_price = account.AvgPrice.get(token, 0)
                        leverage = account.Leverage.get(token, 1)
                        if avg_price == 0:
                            return
                        usd = token_balance * avg_price  * (1 + leverage * (order.Price-avg_price)/avg_price)
                        amount = usd  * (1 - fee) / order.Price
                        new_asset = {
                            "asset": amount * (-1),
                            "usd": 0.0,
                        }
                        account.Portfolio[token] = new_asset
                        account.AvgPrice[token] = order.Price
                        account.Leverage[token] = order.Leverage 

        self.accounts[address] = account
        print("Finished processing order, token_address: {}".format(
              order.Token))        
        return


def evaluate_account(account: Account, prices: Dict[str, float]):
    unrealized: float = 0
    position = {}
    # prices = get_latest_price()
    for token, asset in account.Portfolio.items():
        latest_price = prices.get(token, 0)
        token_balance = asset.get("asset", 0)
        position_value = 0
        status = 0
        if token_balance > 0:
            avg_price = account.AvgPrice.get(token, 0)
            leverage = account.Leverage.get(token, 1)
            status = 1
            usd = token_balance * avg_price * (1 + leverage * (latest_price - avg_price) / avg_price)
            unrealized += (usd - token_balance * avg_price)
            position_value = usd
        elif token_balance < 0:
            avg_price = account.AvgPrice.get(token, 0)
            leverage = account.Leverage.get(token, 1)
            usd = (-token_balance) * avg_price * (1 - leverage * (latest_price - avg_price) / avg_price)
            unrealized += (usd - (-token_balance) * avg_price)
            status = 2
            position_value = usd
        else:
            position_value = asset["usd"]
        # usd_balance += asset["usd"]
        position_data = {
            "status": status,
            "roi": (position_value - 10.0) / 10.0 * 100,
            "value": position_value,
            "total": 0,
            "win": 0
        }
        position[token] = position_data

    pnl = account.Profit + unrealized
    roi = pnl / account.InitialBalance * 100

    win = 0
    total_trades = len(account.WinRate.keys())
    for value in account.WinRate.values():
        if value > 0:
            win += 1
    win_rate = float(win / total_trades) if total_trades > 0 else 0.0

    for id, value in account.WinRate.items():
        token = account.TokenRate.get(id, "")
        if token == "":
            continue
        position[token]["total"] = position[token].get("total") + 1
        if value > 0:
            position[token]["win"] = position[token].get("win") + 1
    return roi, win_rate, position

def get_latest_price(addr: str, pub_key: str, timestamp: int, signature: str, latesttime: int = 0) -> Union[dict, None]:
    config_file = 'env/config.ini'
    config = Config(config_file)
    url = config.api.get("url") + "getlatestprice"
    params = {
        "userId": addr,
        "pubKey": pub_key,
        "timestamp": timestamp,
        "sig": signature
    } 
    if latesttime > 0: 
        params["latesttime"] = latesttime
    resp = requests.get(url, params=params, timeout=25)
    if resp.status_code != 200:
        return {}
    json_resp = json.loads(resp.text)
    if json_resp.get("code") == 200 and json_resp.get("data"):
        result = {}
        for price_data in json_resp["data"]:
            price = price_data['Price']
            token = price_data['TokenAddress']
            result[token] = price
        return result
    else:
        return {}
    
def get_recent_orders(addr: str, pub_key: str, timestamp: int, signature: str, tradetime: int = 0) -> Union[List, None]:
    config_file = 'env/config.ini'
    config = Config(config_file)
    url = config.api.get("url") + "getalltrades"
    params = {
        "userId": addr,
        "pubKey": pub_key,
        "timestamp": timestamp,
        "sig": signature,
    }
    if tradetime > 0:
        params["tradetime"] = tradetime
    resp = requests.get(url, params=params, timeout=25)
    if resp.status_code != 200:
        return []
    json_resp = json.loads(resp.text)
    order_list = []
    if json_resp.get("code") == 200 and json_resp.get("data"):
        for order_data in json_resp["data"]:
            order = Order(
                MinerId=order_data.get("MinerID", ""),
                Token=order_data.get("TokenAddress", ""),
                isClose=(order_data.get("PositionManager", "") == "close"),
                Direction=order_data.get("Direction", 0),
                Nonce=order_data.get("Nonce", 0),
                Price=order_data.get("TradePrice", 0),
                Price4H=order_data.get("TradePrice4H", 0),
                TimeStamp=order_data.get("Timestamp", 0),
                Leverage=order_data.get("Leverage", 1),
            )
            order_list.append(order)
        order_list.sort(key=lambda x: x.TimeStamp)
        return order_list
    else:
        return []


def get_miner_registertime(addr: str, pub_key: str, timestamp: int, signature: str, starttime: int) -> dict:
    config_file = 'env/config.ini'
    config = Config(config_file)
    url = config.api.get("url") + "getregistertime"
    result = dict()
    params = {
        "userId": addr,
        "pubKey": pub_key,
        "timestamp": timestamp,
        "sig": signature,
        "starttime": starttime
    }
    resp = requests.get(url, params=params, timeout=25)
    if resp.status_code != 200:
        return result
    json_resp = json.loads(resp.text)

    if json_resp.get("code") == 200 and json_resp.get("data"):
        for data in json_resp["data"]:
            address = data.get('Address')
            register_time = data.get('RegisterTime')
            if not address or not register_time:
                continue
            result[address] = int(register_time)
    return result

def format_data(data: Union[List, Dict, tuple, str]) -> bytes:
    '''
    format data to str message
    :param data:
    :type data:
    :return:
    :rtype:
    '''
    if isinstance(data, dict):
        sorted_data = sorted(data.items(), key=lambda x: x[0])
        message = ''.join(str(value) for _, value in sorted_data)
    elif isinstance(data, (list, tuple)):
        message = ''.join(str(value) for key, value in data)
    else:
        message = data
    return message.encode()
