import json
from typing import Dict, List, Union

import requests

from config import Config

DEFAULT_TOKENS = ["0x514910771af9ca656af840dff83e8264ecf986ca","0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
                  "0x6982508145454ce325ddbe47a25d4ec3d2311933","0xaea46a60368a7bd060eec7df8cba43b7ef41ad85",
                  "0x808507121b80c02388fad14726482e061b8da827","0x9d65ff81a3c488d585bbfb0bfe3c7707c7917f54",
                  "0x6e2a43be0b1d33b726f0ca3b8de60b3482b8b050","0xc18360217d8f7ab5e7c516566761ea12ce7f9d72",
                  "0xa9b1eb5908cfc3cdf91f9b8b3a74108598009096","0x57e114b691db790c35207b2e685d4a43181e6061"]

class Account:
    def __init__(self,Portfolio={}, AvgPrice = None, WinRate = None,Balance=100, TimeStamp = 0):
        self.Portfolio = Portfolio
        self.InitialBalance = Balance
        self.AvgPrice = {} if AvgPrice is None else AvgPrice.copy()
        self.FirstTrade = TimeStamp
        self.WinRate = {} if WinRate is None else WinRate.copy()

def init_account(account_id: str):
    portfolio = {}
    for item in DEFAULT_TOKENS:
        asset = {
            "asset" : 0.0,
            "usd": 10.0
        }
        portfolio[item] = asset
    account = Account(portfolio)
    return account
    

class Order:
    def __init__(self, MinerId="", Token="", isClose = False, Direction=0, Nonce=0, Price=0, Price4H=0, TimeStamp=0):
        self.MinerId = MinerId
        self.Token = Token
        self.isClose = isClose
        self.Direction = Direction
        self.Nonce = Nonce
        self.Price = Price
        self.Price4H = Price4H
        self.TimeStamp = TimeStamp
    
def process_order(accounts: Dict[str, Account], order: Order, latest_price: Dict[str, float]):
    address = order.MinerId
    token = order.Token
    # validate miner
    if address not in accounts.keys():
        return
    account = accounts.get(address)
    if account.FirstTrade == 0 or account.FirstTrade > order.TimeStamp:
        account.FirstTrade = order.TimeStamp
    # calculate winrate, only calculate open order
    if not order.isClose:
        if order.Price4H == 0:
            order.Price4H = latest_price.get(token, 0)
        if order.Price < order.Price4H and order.Direction == 1:
            account.WinRate[order.Nonce] = 1
        elif order.Price > order.Price4H and order.Direction == -1:
            account.WinRate[order.Nonce] = 1
        else:
            account.WinRate[order.Nonce] = 0
            
    # calculate portfolio
    asset = account.Portfolio.get(token, {})
    if order.isClose:
        new_asset = {
            "asset" : 0.0,
        }
        balance = asset.get("asset", 0)
        if balance > 0 :
            usd = balance * order.Price
        else:
            avg_price = account.AvgPrice.get(token, 0)
            if avg_price == 0:
                return
            usd = (-balance) * avg_price  * (1 -(order.Price-avg_price)/avg_price)
        new_asset["usd"] = usd
        account.Portfolio[token] = new_asset
        account.AvgPrice[token] = 0
    else:
        if order.Direction == 1:
            usd_balance = asset.get("usd", 0)
            if usd_balance > 0:  
                new_asset = {
                    "usd" : 0.0,
                    "asset": usd_balance / order.Price
                }
                account.Portfolio[token] = new_asset
                account.AvgPrice[token] = order.Price
            else:
                token_balance = asset.get("asset", 0)
                if token_balance < 0:
                    avg_price = account.AvgPrice.get(token, 0)
                    if avg_price == 0:
                        return
                    usd = (-token_balance) * avg_price  * (1 -(order.Price-avg_price)/avg_price)
                    amount = usd / order.Price
                    new_asset = {
                        "asset": amount,
                        "usd": 0.0,
                    }
                    account.Portfolio[token] = new_asset
                    account.AvgPrice[token] = order.Price                   
        else:
            usd_balance = asset.get("usd", 0)
            if usd_balance > 0:  
                new_asset = {
                    "usd" : 0.0,
                    "asset": usd_balance / order.Price * (-1)
                }
                account.Portfolio[token] = new_asset
                account.AvgPrice[token] = order.Price
            else:
                token_balance = asset.get("asset", 0)
                if token_balance > 0:
                    new_asset = {
                        "asset": token_balance * (-1),
                        "usd": 0.0,
                    }
                    account.Portfolio[token] = new_asset
                    account.AvgPrice[token] = order.Price                  
                 
    accounts[address] = account
    print("Finished processing order, token_address: {}".format(
          order.Token))        
    return

def evaluate_account(account: Account, prices: Dict[str, float]):
    unrealized: float = 0
    usd_balance: float = 0
    # prices = get_latest_price()
    for token, asset in account.Portfolio.items():
        latest_price = prices.get(token, 0)
        token_balance = asset.get("asset", 0)
        if token_balance > 0:
            unrealized += latest_price * token_balance
        elif token_balance < 0:
            avg_price = account.AvgPrice.get(token, 0)
            usd = (-token_balance) * avg_price  * (1 -(latest_price-avg_price)/avg_price)
            unrealized += usd
        usd_balance += asset["usd"]

    pnl = usd_balance + unrealized - account.InitialBalance
    roi = pnl / account.InitialBalance * 100
    
    win = 0
    total_trades = len(account.WinRate.keys())
    for value in account.WinRate.values():
        if value > 0:
            win += 1
    win_rate = float(win/total_trades) if total_trades > 0 else 0.0
    return roi, win_rate  

def get_latest_price(addr: str, pub_key: str, timestamp: int, signature: str) -> Union[dict, None]:
    config_file = 'env/config.ini'
    config = Config(config_file)    
    url = config.api.get("url") + "getlatestprice" 
    params = {
        "userId": addr,
        "pubKey": pub_key,
        "timestamp": timestamp,
        "sig": signature
    }    
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
    
def get_recent_orders(addr: str, pub_key: str, timestamp: int, signature: str) -> Union[List, None]:
    config_file = 'env/config.ini'
    config = Config(config_file)
    url = config.api.get("url") + "getalltrades"
    params = {
        "userId": addr,
        "pubKey": pub_key,
        "timestamp": timestamp,
        "sig": signature
    }
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
                TimeStamp=order_data.get("Timestamp", 0)
            )
            order_list.append(order)
        order_list.sort(key=lambda x: x.TimeStamp)
        return order_list
    else:
        return []
