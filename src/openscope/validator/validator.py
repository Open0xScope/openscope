import argparse
import asyncio
import time
from datetime import datetime
from os.path import dirname, realpath

from communex._common import get_node_url
from communex.client import CommuneClient
from communex.compat.key import check_ss58_address, classic_load_key
from communex.module.module import Module
from communex.types import Ss58Address
from config import Config
from substrateinterface import Keypair
from trade import *


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

    # cut_weights = cut_to_max_allowed_weights(score_dict)
    # adjsuted_to_sigmoid = threshold_sigmoid_reward_distribution(cut_weights)

    # Create a new dictionary to store the weighted scores
    weighted_scores: dict[int, int] = {}
    top_10, top_25, top_50 = 0, 0, 0
    # Calculate the sum of all inverted scores
    for score in score_dict.values():
        if score == 1:
            top_10 += 1
        elif score == 2:
            top_25 += 1
        elif score == 3:
            top_50 += 1

    for uid, score in score_dict.items():
        if score == 1:
            weight = int(30 / top_10)
        elif score == 2:
            weight = int(60 / top_25)
        elif score == 3:
            weight = int(40 / top_50)
        else:
            weight = 0
        # Add the weighted score to the new dictionary
        weighted_scores[uid] = int(weight)

    remain_weight = 100 - sum(weighted_scores.values())
    for uid in score_dict.keys():
        score = weighted_scores.get(uid, 0)
        weighted_scores[uid] = int(score +(remain_weight/len(score_dict.keys())))
    
    # filter out 0 weights
    weighted_scores = {k: v for k, v in weighted_scores.items() if v != 0}
    uids = list(weighted_scores.keys())        
    weights = list(weighted_scores.values())

    print(f"weights for the following uids: {uids}")
    if len(uids) > 0:
        client.vote(key=key, uids=uids, weights=weights, netuid=netuid)
    return weighted_scores


def cut_to_max_allowed_weights(
    score_dict: dict[int, float], config: Config | None = None
) -> dict[int, float]:
    """
    Cuts the scores to the maximum allowed weights.

    Args:
        score_dict (dict[int, float]): A dictionary mapping miner UIDs to their scores.

    Returns:
            dict[int, float]: A dictionary mapping miner UIDs to their scores,
            where the scores have been cut to the maximum allowed weights.
    """

    # max_allowed_weights = config.max_allowed_weights
    max_allowed_weights = 100
    
    # sort the score by highest to lowest
    sorted_scores = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)

    # cut to max_allowed_weights
    cut_scores = sorted_scores[:max_allowed_weights]

    return dict(cut_scores)


def get_netuid(clinet: CommuneClient, subnet_name: str = "oxScope"):
    """
    Retrieves the network UID of the subnet.

    Args:
        client (CommuneClient): The CommuneX client.
        subnet_name (str, optional): The name of the subnet. Defaults to "oxScope".

    Returns:
        int: The network UID of the subnet.
    """

    subnets = clinet.query_map_subnet_names()
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
            
        orders = get_recent_orders()
        for order in orders:
            process_order(accounts, order)
        roi_data = {}
        for uid, account in accounts.items():
            if account.FirstTrade > 0:
                roi = evaluate_account(account)
                roi_data[uid] = roi
                print(f"{uid} roi data: {roi}")
        scores = self.generate_scores(roi_data)
        for address in scores.keys():
            if address != self.key.ss58_address:
            # score has to be lower or eq to 1, as one is the best score
                uid = uid_map[address]
                if uid is None:
                    raise ValueError(
                    f"{address} is not registered in subnet"
                    )
                score_dict[uid] = scores.get(address, 0)

        if not score_dict:
            print("No miner managed to give a valid answer")
            return {}
        weighted_scores = set_weights(score_dict, self.netuid, self.client, self.key)

        return weighted_scores

    def generate_scores(self, data: dict[str, float]):
        score_dict = {}
        sorted_addresses = sorted(data.items(), key=lambda x: x[1], reverse=True)
        total_addresses = len(sorted_addresses)
        # top_10_percent = int(total_addresses * 0.1)
        next_15_percent = int(total_addresses * 0.25)
        next_25_percent = int(total_addresses * 0.5)

        # top_10_addresses = [address[0] for address in sorted_addresses[:top_10_percent]]
        next_15_addresses = [address[0] for address in sorted_addresses[:next_15_percent]]
        next_25_addresses = [address[0] for address in sorted_addresses[next_15_percent:next_25_percent]]
        last_50_addresses = [address[0] for address in sorted_addresses[next_25_percent:]]


        # for address in top_10_addresses:
        #     score_dict[address] = 1
        for address in next_15_addresses:
            score_dict[address] = 2
        for address in next_25_addresses:
            score_dict[address] = 3
        for address in last_50_addresses:
            score_dict[address] = 0
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
                print(f"Upload attempt {attempt} failed: {e}")
                attempt += 1
                if attempt > max_attempts:
                    print("Could not upload data. ")
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

    # 检查用户是否提供了--config参数
    if args.config is None:
        default_config_path = 'env/config.ini'
        config_file = default_config_path
    else:
        config_file = args.config
    config = Config(config_file=config_file)
    c_client = CommuneClient(get_node_url(use_testnet=True))
    synthia_uid = get_netuid(c_client)
    keypair = classic_load_key(config.validator.get("keyfile"))

    validator = TradeValidator(
        keypair, 
        synthia_uid, 
        c_client, 
        call_timeout=60,
    )
    validator.validation_loop(config)