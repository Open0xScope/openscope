import argparse
import asyncio
import time
from datetime import datetime
from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import check_ss58_address, classic_load_key
from communex.module.module import Module
from communex.types import Ss58Address
import sr25519
from config import Config
from substrateinterface import Keypair
from trade import *

from loguru import logger

logger.add("logs/log_{time:YYYY-MM-DD}.log", rotation="1 day")


def set_weights(
    score_dict: dict[int, float], netuid: int, client: CommuneClient, key: Keypair
) -> None:
    """
    Set weights for miners based on their scores.

    The lower the score, the higher the weight.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.
        netuid (int): The network UID.
        client (CommuneClient): The CommuneX client.
        key (Keypair): The keypair for signing transactions.
    """
    # Create a new dictionary to store the weighted scores
    sorted_score = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
    sorted_ids = [key for key, value in sorted_score]

    total_ids = len(sorted_ids)
    half_ids = total_ids // 2
    min_weight = 500 / half_ids
    max_weight = 3 * min_weight
    common_diff = (max_weight - min_weight) / (half_ids - 1)
    weights = [max_weight - i * common_diff for i in range(half_ids)]

    # Add the weighted score to the new dictionary
    weighted_scores = {}
    for i in range(half_ids):
        weighted_scores[sorted_ids[i]] = int(weights[i])
    
    remain_weight = 1000 - sum(weighted_scores.values())
    for uid in weighted_scores.keys():
        score = weighted_scores.get(uid, 0)
        weighted_scores[uid] = int(score +(remain_weight/half_ids))
    

    # filter out 0 weights
    weighted_scores = {k: v for k, v in weighted_scores.items() if v > 0}
    uids = list(weighted_scores.keys())        
    weights = list(weighted_scores.values())

    logger.info(f"weights for the following uids: {uids}")
    if len(uids) > 0:
        client.vote(key=key, uids=uids, weights=weights, netuid=netuid)
    return weighted_scores


def _format_data(data: Union[List, Dict, tuple, str]) -> bytes:
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
    """A class for calculating roi data using a Synthia network.
    """

    def __init__(
        self,
        key: Keypair,
        netuid: int,
        client: CommuneClient,
        call_timeout: int = 60,
    ) -> None:
        super().__init__()
        self.client = client
        self.key = key
        self.netuid = netuid
        self.call_timeout = call_timeout

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
        self, config: Config, syntia_netuid: int
    ) -> list[dict[str, str]]:
        # modules_adresses = self.get_modules(self.client, syntia_netuid)
        modules_keys = self.client.query_map_key(syntia_netuid)
        val_ss58 = self.key.ss58_address
        if val_ss58 not in modules_keys.values():
            raise ValueError(
                f"validator key {val_ss58} is not registered in subnet"
                )
        # Validation
        score_dict: dict[int, float] = {}
        
        # == Validation loop / Scoring ==
        accounts = {}
        uid_map = {}
        for uid, address in modules_keys.items():
            account = init_account(address) 
            accounts[address] = account
            uid_map[address] = uid
        
        timestamp = int(time.time())
        pub_key = keypair.public_key.hex()
        msg = f'{val_ss58}{pub_key}{timestamp}'
        message = _format_data(msg)
        signature = sr25519.sign(  # type: ignore
                (keypair.public_key, keypair.private_key), message).hex()  # type: ignore
        orders = get_recent_orders(val_ss58, pub_key, timestamp, signature)
        latest_price = get_latest_price(val_ss58, pub_key, timestamp, signature)
        for order in orders:
            process_order(accounts, order, latest_price)
        roi_data = {}
        win_data = {}
        for uid, account in accounts.items():
            if account.FirstTrade > 0:
                roi, win_rate = evaluate_account(account, latest_price)
                roi_data[uid] = roi
                win_data[uid] = win_rate
                logger.info(f"{uid} roi data: {roi}, win rate: {win_rate}")
        scores = self.generate_scores(roi_data, win_data)
        for address in scores.keys():
            # score has to be lower or eq to 1, as one is the best score
            uid = uid_map[address]
            if uid is None:
                raise ValueError(
                f"{address} is not registered in subnet"
                )
            score_dict[uid] = scores.get(address, 0)

        if not score_dict:
            logger.info("No miner managed to give a valid answer")
            return {}
        weighted_scores = set_weights(score_dict, self.netuid, self.client, self.key)

        return weighted_scores

    def generate_scores(self, roi_data: dict[str, float], win_data: dict[str, float]):
        score_dict = {}
        if roi_data:
            max_score = max(roi_data.values())
            min_score = min(roi_data.values())
            for uid, score in roi_data.items():
                roi_score = float((score - min_score) / (max_score - min_score))
                win_score = win_data.get(uid, 0)
                score = 0.8 * roi_score + 0.2 * win_score
                score_dict[uid] = score
        return score_dict
    
    def upload_data(
        self, data: list[dict[str, str]]
    ) -> None:
        """Uploads the validation data.

        Args:
            data: A dictionary containing the validation data to upload.
        """
        max_attempts = 3
        attempt = 1
        upload_dict = {"data_list": data}
        while attempt <= max_attempts:
            try:

                # _ = upload_dict()
                break
            except requests.exceptions.RequestException as e:
                logger.info(f"Upload attempt {attempt} failed: {e}")
                attempt += 1
                if attempt > max_attempts:
                    logger.info("Could not upload data. ")
                    break
    

    def validation_loop(self, config: Config | None = None) -> None:
        # Run validation
        while True:
            start_time = time.time()
            formatted_start_time = datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"check validator time: {formatted_start_time}")
            weighted_scores = asyncio.run(self.validate_step(config, self.netuid))
            print(f"vote data: {weighted_scores}")
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
    synthia_uid = get_netuid(c_client)
    keypair = classic_load_key(config.validator.get("keyfile"))

    validator = TradeValidator(
        keypair, 
        synthia_uid, 
        c_client, 
        call_timeout=60,
    )
    validator.validation_loop(config)