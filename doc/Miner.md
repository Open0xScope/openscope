
## Prerequisite

### Install Dependencies

```
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
    - **url**: http://127.0.0.1:5005/ (IP address and port where the miner service is running)
    ```

2. **Register the Miner**: Before running the miner, you need to register it. Use the following command:

    ```bash
    comx module register <name> <your_commune_key> --netuid <0xscope netuid>
    ```

OpenScope Testnet netuid:14.

3. **Serve the Miner**: Start the miner server by running the following command:

    ```bash
    python src/openscope/miner/signal_trade.py
    ```

    Note: You need to keep this process alive, running in the background. Some options are `nohup`.

4. **Send a Trade**: You can send an order using the following Python script:

    ```bash
    python src/openscope/tests/trade.py
    ```

    or

    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"token": "0x514910771af9ca656af840dff83e8264ecf986ca", "position_manager": "open", "direction": 1}' http://127.0.0.1:8080/trade
    ```

## Running the Event Subscription Services

You should subscribe event data provide by OpenScope team, these event data is required for tranning event-driven models and direct you to make trades.

Read more about this [here](../README.md)

1. **Subscribing to Historical Events**: To subscribe to historical events, run the following Python script:

    ```bash
    python src/openscope/miner/event_subscription.py -history
    ```

[Where the Data goes]

2. **Subscribing to Real-Time Events**: To subscribe to real-time events, run the following Python script:

    ```bash
    python src/openscope/miner/event_subscription.py
    ```

    Note: You need to keep this process alive, running in the background. Some options are `nohup`.
