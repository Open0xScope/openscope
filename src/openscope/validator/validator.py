import argparse
import asyncio
from datetime import datetime
import numpy
import pandas
import time
import threading
import requests
import sr25519
from communex.client import CommuneClient
from communex.module.module import Module
from communex.compat.key import check_ss58_address
from communex.types import Ss58Address
from substrateinterface import Keypair
from communex._common import get_node_url
from communex.compat.key import classic_load_key
from os.path import dirname, realpath
from loguru import logger
from threading import Timer

from config import Config
from stats import calculate_serenity
from trade import *
from eliminate import *

logger.add("logs/log_{time:YYYY-MM-DD}.log", rotation="1 day")

ELIMINATE_MINER = dict()
ELIMINATE_FILE = str()
PROTECT_ADDRESS = list()
NOT_ACTIVE_ELIMINATION_TARGET_TIME = 0
COPY_TRADING_ELIMINATION_TARGET_TIME = 0
PROTECT_ADDRESS_TARGET_TIME = 0
MDD_ELIMINATION_TARGET_TIME = 0
DEFAULT_WEIGHT = 5


def set_weights(
        score_dict: dict[int, float], netuid: int, client: CommuneClient, key: Keypair, elimated_ids: list[int]
) -> None:
    """
    Set weights for miners based on their scores.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.
        netuid (int): The network UID.
        client (CommuneClient): The CommuneX client.
        key (Keypair): The keypair for signing transactions.
    """
    filtered_score_dict = {miner_id: score for miner_id, score in score_dict.items() if miner_id not in elimated_ids}

    # Create a new dictionary to store the weighted scores
    sorted_score = sorted(filtered_score_dict.items(), key=lambda x: x[1], reverse=True)
    sorted_ids = [key for key, value in sorted_score]
    total_miners = len(sorted_score)

    if total_miners < 100:
        top_3_threshold = int(total_miners * 0.03)
        top_10_threshold = int(total_miners * 0.1)
        top_25_threshold = int(total_miners * 0.25)
        top_50_threshold = int(total_miners * 0.5)
    else:
        top_3_threshold = 3
        top_10_threshold = 10
        top_25_threshold = 25
        top_50_threshold = 50

    # Add the weighted score to the new dictionary
    weighted_scores = {}
    for i, (miner_uid, score) in enumerate(sorted_score):
        if i < top_3_threshold:
            total_score_in_group = sum(filtered_score_dict[uid[0]] for uid in sorted_score[:top_3_threshold])
            weight_share = score / total_score_in_group
            weighted_scores[miner_uid] = int(weight_share * 0.25 * 1000)
        elif i < top_10_threshold:
            total_score_in_group = sum(
                filtered_score_dict[uid[0]] for uid in sorted_score[top_3_threshold:top_10_threshold])
            weight_share = score / total_score_in_group
            weighted_scores[miner_uid] = int(weight_share * 0.25 * 1000)
        elif i < top_25_threshold:
            total_score_in_group = sum(
                filtered_score_dict[uid[0]] for uid in sorted_score[top_10_threshold:top_25_threshold])
            weight_share = score / total_score_in_group
            weighted_scores[miner_uid] = int(weight_share * 0.25 * 1000)
        elif i < top_50_threshold:
            total_score_in_group = sum(
                filtered_score_dict[uid[0]] for uid in sorted_score[top_25_threshold:top_50_threshold])
            weight_share = score / total_score_in_group
            weighted_scores[miner_uid] = int(weight_share * 0.25 * 1000)
        else:
            weighted_scores[miner_uid] = 0

    remain_weight = 1000 - sum(weighted_scores.values())
    for item in sorted_score[:top_50_threshold]:
        uid = item[0]
        score = weighted_scores.get(uid, 0)
        weighted_scores[uid] = int(score + (remain_weight / top_50_threshold))

    # filter out 0 weights
    weighted_scores = {k: v for k, v in weighted_scores.items() if v > 0}
    uids = list(weighted_scores.keys())
    weights = list(weighted_scores.values())

    logger.info(f"weights for the following uids: {uids}")
    if len(uids) > 0:
        client.vote(key=key, uids=uids, weights=weights, netuid=netuid)

    for id in sorted_ids:
        if id not in weighted_scores.keys():
            weighted_scores[id] = 0
    return weighted_scores


def get_netuid(client: CommuneClient, subnet_name: str = "OpenScope"):
    """
    Retrieves the network UID of the subnet.

    Args:
        client (CommuneClient): The CommuneX client.
        subnet_name (str, optional): The name of the subnet. Defaults to "OpenScope".

    Returns:
        int: The network UID of the subnet.
    """

    subnets = client.query_map_subnet_names()
    for netuid, name in subnets.items():
        if name == subnet_name:
            return netuid
    raise ValueError(f"Subnet {subnet_name} not found")


class TradeValidator(Module):
    """A class for calculating roi data using a Openscope network.
    """

    def __init__(
            self,
            key: Keypair,
            netuid: int,
            client: CommuneClient,
            account_manager: AccountManager,
            call_timeout: int = 60,
    ) -> None:
        super().__init__()
        self.client = client
        self.key = key
        self.netuid = netuid
        self.call_timeout = call_timeout
        self.account_manager = account_manager

    def get_modules(self, client: CommuneClient, netuid: int) -> dict[int, str]:
        """Retrieves all module addresses from the subnet.

        Args:
            client: The CommuneClient instance used to query the subnet.
            netuid: The unique identifier of the subnet.

        Returns:
            A list of module addresses as strings.
        """
        module_addreses = client.query_map_address(netuid)
        return module_addreses

    async def validate_step(
            self, config: Config, netuid: int
    ) -> list[dict[str, str]]:
        # modules_adresses = self.get_modules(self.client, netuid)
        modules_keys = self.client.query_map_key(netuid)
        val_ss58 = self.key.ss58_address
        if val_ss58 not in modules_keys.values():
            raise ValueError(
                f"validator key {val_ss58} is not registered in subnet"
            )
        # Validation
        score_dict: dict[int, float] = {}

        # == Validation loop / Scoring ==
        self.account_manager.load_positions_in_memory()
        uid_map = {}
        for uid, address in modules_keys.items():
            account = self.account_manager.accounts.get(address, {})
            if account == {}:
                account = init_account()
                self.account_manager.accounts[address] = account
            uid_map[address] = uid

        timestamp = int(time.time())
        tradetime = self.account_manager.get_update_time()
        pub_key = keypair.public_key.hex()
        msg = f'{val_ss58}{pub_key}{timestamp}'
        message = format_data(msg)
        signature = sr25519.sign(  # type: ignore
            (keypair.public_key, keypair.private_key), message).hex()  # type: ignore
        orders = get_recent_orders(val_ss58, pub_key, timestamp, signature, tradetime)
        self.account_manager.group_orders_by_day(orders=orders)
        latest_price = get_latest_price(val_ss58, pub_key, timestamp, signature)

        roi_data, win_data, position_data = self.account_manager.process_orders_by_day(latest_price, val_ss58, pub_key,
                                                                                       keypair)
        serenity_data = {}
        mdd_data = {}
        return_data, change_data, mdd_list = self.account_manager.generate_returns()
        for id, return_list in return_data.items():
            change_list = change_data[id]
            if id in mdd_list:
                continue
            returns = pandas.Series(return_list)
            changes = pandas.Series(change_list)
            serenity_value, mdd_value = calculate_serenity(returns, changes)
            if numpy.isnan(serenity_value):
                serenity_value = 0.0
            serenity_data[id] = float(serenity_value)
            mdd_data[id] = float(mdd_value)
            logger.info(f'id: {id}, serenity: {float(serenity_value)}, mdd: {float(mdd_value)}')
        scores = self.generate_scores(mdd_data, serenity_data)
        for address in scores.keys():
            uid = uid_map[address]
            if uid is None:
                raise ValueError(
                    f"{address} is not registered in subnet"
                )
            score_dict[uid] = scores.get(address, 0)

        if not score_dict:
            logger.info("No miner managed to give a valid answer")
            return {}

        elimated_ids = []
        for address, status in ELIMINATE_MINER.items():
            if not status['status']:
                continue
            uid = uid_map[address]
            logger.info(f"{address} is eliminated")
            if uid is None:
                logger.info(f"{address} is not registered in subnet")
                continue
            elimated_ids.append(uid)
        if len(self.account_manager.checkpoints) > 2:
            weighted_scores = set_weights(score_dict, self.netuid, self.client, self.key, elimated_ids)
        else:
            weighted_scores = {}
            for uid in modules_keys.keys():
                weighted_scores[uid] = DEFAULT_WEIGHT
            uids = list(weighted_scores.keys())
            weights = list(weighted_scores.values())
            logger.info(f"weights for the following uids: {uids}")
            self.client.vote(key=self.key, uids=uids, weights=weights, netuid=self.netuid)
        return weighted_scores, modules_keys, win_data, roi_data

    def generate_scores(self, mdd_data: dict[str, float], serenity_data: dict[str, float]):
        score_dict = {}
        if mdd_data:
            max_serenity = max(serenity_data.values())
            min_serenity = min(serenity_data.values())
            for uid, score in mdd_data.items():
                mdd_value = abs(mdd_data.get(uid, 0)) * 100
                coffiecient = 1.0
                if mdd_value > 20:
                    coffiecient = 0.7
                elif mdd_value > 10:
                    coffiecient = 0.9
                serenity = serenity_data.get(uid, 0.0)
                serenity_score = float((serenity - min_serenity) / (max_serenity - min_serenity))
                # win_score = win_data.get(uid, 0)
                score = serenity_score * coffiecient
                score_dict[uid] = score
        return score_dict

    @staticmethod
    def unixtime2str(unixtime=None, t_format='%Y-%m-%d %H:%M:%S', utc=True):
        if unixtime is None:
            unixtime = datetime.now().timestamp()
        unixtime = int(unixtime)
        if utc:
            ret = datetime.utcfromtimestamp(unixtime).strftime(t_format)
        else:
            ret = datetime.fromtimestamp(unixtime).strftime(t_format)
        return ret

    def task_get_protect_address(self):
        global ELIMINATE_MINER, PROTECT_ADDRESS
        logger.info(f"task_get_protect_address begin")
        PROTECT_ADDRESS = get_protected_miner(keypair)
        logger.info(f'PROTECT_ADDRESS: {len(PROTECT_ADDRESS)}')
        for address in PROTECT_ADDRESS:
            ELIMINATE_MINER[address] = {'status': False, 'timestamp': self.unixtime2str(), 'reason': 'protect_address'}
        save_eliminate_data(ELIMINATE_MINER, file=ELIMINATE_FILE)
        logger.info(f"task_get_protect_address end")

    def task_mdd_elimination(self):
        global ELIMINATE_MINER
        logger.info(f"task_mdd_elimination begin")
        address = mdd_elimination(checkpoints=account_manager.checkpoints)
        roi_data = {}
        if address:
            for value in account_manager.checkpoints:
                last_update = value.last_update
                rois = value.roi
                last_update_day = self.unixtime2str(last_update, t_format='%Y-%m-%d')
                roi_data[last_update_day] = {}
                for k, roi in rois.items():
                    if k in address:
                        roi_data[last_update_day][k] = roi

            logger.info(f'elimination:: mdd_elimination: {address}, roi_data: {roi_data}')
        else:
            logger.info(f'mdd_elimination get nothing')
        eliminate_address = set(address) - set(PROTECT_ADDRESS)
        for x in eliminate_address:
            if x not in ELIMINATE_MINER or not ELIMINATE_MINER[x]['status']:
                ELIMINATE_MINER[x] = {'status': True, 'timestamp': self.unixtime2str(), 'reason': 'mdd_elimination'}
        logger.info(f"task_mdd_elimination end")

    def task_copy_trading_elimination(self):
        global ELIMINATE_MINER
        logger.info(f"task_copy_trading_elimination begin")
        copy_maps = copy_trading_elimination(keypair)
        if copy_maps:
            logger.info(f'elimination:: copy_trading_elimination: {copy_maps}')
        else:
            logger.info(f'copy_trading_elimination get nothing')
        eliminate_address = set(copy_maps.keys()) - set(PROTECT_ADDRESS)
        for x in eliminate_address:
            if x not in ELIMINATE_MINER or not ELIMINATE_MINER[x]['status']:
                ELIMINATE_MINER[x] = {'status': True, 'timestamp': self.unixtime2str(), 'reason': 'copy_trading_elimination'}
        logger.info(f"task_copy_trading_elimination end")

    def task_not_active_elimination(self):
        global ELIMINATE_MINER
        logger.info(f"task_not_active_elimination begin")
        address = not_active_elimination(keypair)
        if address:
            logger.info(f'elimination:: not_active_elimination: {address}')
        else:
            logger.info(f'not_active_elimination get nothing')
        eliminate_address = set(address) - set(PROTECT_ADDRESS)
        for x in eliminate_address:
            if x not in ELIMINATE_MINER or not ELIMINATE_MINER[x]['status']:
                ELIMINATE_MINER[x] = {'status': True, 'timestamp': self.unixtime2str(), 'reason': 'not_active_elimination'}
        logger.info(f"task_not_active_elimination end")

    def timer_func(self):
        global NOT_ACTIVE_ELIMINATION_TARGET_TIME, COPY_TRADING_ELIMINATION_TARGET_TIME, PROTECT_ADDRESS_TARGET_TIME, MDD_ELIMINATION_TARGET_TIME
        current_time = int(time.time())
        logger.info(f'''timer_func begin''')
        if current_time >= PROTECT_ADDRESS_TARGET_TIME:
            self.task_get_protect_address()
            PROTECT_ADDRESS_TARGET_TIME = current_time + 300

        if current_time >= NOT_ACTIVE_ELIMINATION_TARGET_TIME:
            self.task_not_active_elimination()
            NOT_ACTIVE_ELIMINATION_TARGET_TIME = current_time + 86400

        if current_time >= COPY_TRADING_ELIMINATION_TARGET_TIME:
            self.task_copy_trading_elimination()
            COPY_TRADING_ELIMINATION_TARGET_TIME = current_time + 86400

        if current_time >= MDD_ELIMINATION_TARGET_TIME:
            self.task_mdd_elimination()
            MDD_ELIMINATION_TARGET_TIME = current_time + 86400
        logger.info(f'''timer_func end:
NOT_ACTIVE_ELIMINATION_TARGET_TIME: {NOT_ACTIVE_ELIMINATION_TARGET_TIME}
COPY_TRADING_ELIMINATION_TARGET_TIME: {COPY_TRADING_ELIMINATION_TARGET_TIME}
PROTECT_ADDRESS_TARGET_TIME: {PROTECT_ADDRESS_TARGET_TIME}
MDD_ELIMINATION_TARGET_TIME: {MDD_ELIMINATION_TARGET_TIME}''')
        Timer(300, self.timer_func).start()

    def start_timer(self):
        timer_thread = threading.Thread(target=self.timer_func)
        timer_thread.daemon = True  # 设置为守护线程
        timer_thread.start()

    def validation_loop(self, config: Config | None = None) -> None:
        global ELIMINATE_MINER, ELIMINATE_FILE
        ELIMINATE_FILE = os.path.join(dirname(realpath(__file__)), f'eliminate_{config.validator.get("keyfile")}.json')
        ELIMINATE_MINER = get_eliminate_data(file=ELIMINATE_FILE)
        self.start_timer()
        start_task_flag = False
        # Run validation
        while True:
            start_time = time.time()
            formatted_start_time = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"check validator time: {formatted_start_time}")
            weighted_scores = asyncio.run(self.validate_step(config, self.netuid))
            print(f"vote data: {weighted_scores}")
            if not start_task_flag:
                logger.info(f'start task exec task_mdd_elimination')
                self.task_mdd_elimination()
                start_task_flag = True
            invertal = int(config.validator.get("interval"))
            time.sleep(invertal)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="transaction validator")
    parser.add_argument("--config", type=str, default=None, help="config file path")
    args = parser.parse_args()

    if args.config is None:
        default_config_path = 'env/config.ini'
        config_file = default_config_path
    else:
        config_file = args.config
    config = Config(config_file=config_file)
    use_testnet = True if config.validator.get("testnet") == "1" else False
    c_client = CommuneClient(get_node_url(use_testnet=use_testnet))
    net_uid = get_netuid(c_client)
    keypair = classic_load_key(config.validator.get("keyfile"))

    account_manager = AccountManager(config=config, logger=logger)
    validator = TradeValidator(
        keypair,
        net_uid,
        c_client,
        account_manager,
        call_timeout=60,
    )
    validator.validation_loop(config)
