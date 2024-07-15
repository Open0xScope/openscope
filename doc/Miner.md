

# Prerequisite

### Clone the Code

```bash
git clone git@github.com:Open0xScope/openscope.git
cd openscope
```

### Install Dependencies

```bash
pip install -r requirements.txt
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
    - **url**: http://127.0.0.1:5000/ (IP address and port where your miner service is running)
   
    [api]
    - **url**: [The trade services url] #For testnet: url = http://47.236.87.93:8000/  mainnet: url = http://8.219.104.233:8000/
    ```

2. **Register the Miner**: Before running the miner, you need to register it. Use the following command:

    ```bash
    comx module register <name> <your_commune_key> --netuid <OpenScope netuid>
    ```

OpenScope netuid: 5

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
    curl -X POST -H "Content-Type: application/json" -d '{"token": "0x514910771af9ca656af840dff83e8264ecf986ca", "position_manager": "open", "direction": 1}' http://127.0.0.1:5000/trade
    ```

5. **IQ50**: Automatically create trades via IQ50 script:
   By executing the IQ50 script, trades can be automatically created for 3 random tokens.
    ```bash
    python src/openscope/miner/IQ50.py
    ```
   Note:  A scheduled task can be created using crontab to execute it at regular intervals.

**Trades Structure:**

- token: the address of the token
- position_manager: open/close

1. open: open a position, you should also specify the direction
2. close: close a position, this means you will liquidate this position and no longer effect by the token price change.

- leverage: min:0.1 max:20
- direction: 1/-1 - 1 means long, -1 means short

## Get the training data

We have already open sourced all the events training data on our huggingface space:

[Event Trading Dataset](https://huggingface.co/datasets/0xscope/web3-trading-analysis)

You can also read the descriptions about these data here:

[Event Rules](https://huggingface.co/datasets/0xscope/event_rules)

Be sure to leverage these data that provided by 0xScope (and 0xScope only) to refine your trading strategies.