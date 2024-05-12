
## Prerequisite

### Install Dependencies

```bash
pip install requirements.txt
```

### Install CommuneX and cli

[Set up Commune](https://communeai.org/docs/installation/setup-commune)

### Get a CommuneX Key

[Key Basics](https://communeai.org/docs/working-with-keys/key-basics)

## Run the Miner

1. **Create Configuration File**: Create a file named `config.ini` in the `env/` folder with the following contents:

    ```ini
    [miner]
    - **keyfile**: comx (created key_name)
    - **url**: http://127.0.0.1:5005/ (IP address and port where your miner service is running)
    ```

2. **Register the Miner**: Before running the miner, you need to register it. Use the following command:

    ```bash
    comx module register <name> <your_commune_key> --netuid <OpenScope netuid>
    ```

OpenScope netuid:

OpenScope Testnet netuid:14.

3. **Serve the Miner**: Start the miner server by running the following command:

    ```bash
    python src/openscope/miner/signal_trade.py
    ```

    Note: You need to keep this process alive, running in the background. Some options are `nohup`.

4. **Send a Trade**: 

Running our basic miner example will automatically help you send the trades.

But you can also send an order to adjust your positions using the following Python script:

    ```bash
    python src/openscope/tests/trade.py
    ```

    or

    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"token": "0x514910771af9ca656af840dff83e8264ecf986ca", "position_manager": "open", "direction": 1}' http://127.0.0.1:8080/trade
    ```

**Trades Structure:**

- token: the address of the token
- position_manager: open/close
1. open: open a position, you should also specify the direction
2. close: close a position, this means you will liquidate this position and no longer effect by the token price change.
- direction: 1/-1 - 1 means long, -1 means short

## Running the Event Subscription Services

### Get Tranning Dataset

You should obatin the event dataset provide by OpenScope team, these event data is required for tranning event-driven models and direct you to make trades.

You can check our open sourced dataset on huggingface:

[Event Dataset](https://huggingface.co/datasets/0xscope/web3-trading-analysis)

Or you can subscribe the historical events about these 10 tokens for the past 3 months:

To do so, you need to run the following Python script:

    ```bash
    python src/openscope/miner/event_subscription.py -history
    ```

Once success, you should have all the events under the openscope/resources folder named historic_events.csv

### Subscribing to Real-Time Events: 

To subscribe to real-time events, run the following Python script:

    ```bash
    python src/openscope/miner/event_subscription.py
    ```

    Note: You need to keep this process alive, running in the background. Some options are `nohup`.
