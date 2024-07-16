import json
from typing import Dict
from datetime import datetime

DEFAULT_ACCOUNTS_LOCATION = "data/accounts.json"

class LocalStorage:
    def __init__(self, config=None, logger=None):
        self.config = config
        self.logger = logger
        self.update_time = 0
        self.accounts = {}

    def get_update_time(self):
        return self.update_time

    def load_positions_in_memory(self):
        location = DEFAULT_ACCOUNTS_LOCATION
        data = self._get_json_file(location)
        if data:
            self.accounts = data.get("accounts", {})
        return data

    def write_positions_to_disk(self, data:str):
        # miners that have already been deregistered.
        location = DEFAULT_ACCOUNTS_LOCATION
        self._write_from_memory_to_disk(location, data)

    def _get_json_file(self, location: str) -> Dict:
        try:
            with open(location, 'r') as f:
                data = json.load(f)
                return data
        except FileNotFoundError:
            self.logger.info(f"File not found: {location}")
            return {}

    def _write_from_memory_to_disk(self, location: str, data:str) -> None:
        try:
            with open(location, 'r') as f:
                old_data = json.load(f)
                old_timestamp = old_data.get("timestamp", 0)
        except FileNotFoundError:
            old_timestamp = 0

        current_timestamp = datetime.now().timestamp()
        if current_timestamp > old_timestamp:
            try:
                with open(location, 'w') as f:
                    json.dump({"accounts": self.accounts, "timestamp": current_timestamp, "data": data}, f, indent=4)
                self.logger.info(f"Updated file: {location}")
            except FileNotFoundError:
                self.logger.error(f"File not found: {location}")
        else:
            self.logger.info(f"File {location} already exists and is newer.")
