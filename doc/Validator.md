## Prerequisite

### Clone the Code

```bash
git clone git@github.com:Open0xScope/openscope.git
cd openscope
```

### Install Dependencies

```bash
pip install requirements.txt
```

### Install CommuneX and cli

[Set up Commune](https://communeai.org/docs/installation/setup-commune)

### Get a CommuneX Key

[Key Basics](https://communeai.org/docs/working-with-keys/key-basics)


## Run the Validator

1. Create a file named config.ini in the env/ folder, you can check the example config.ini.sample for reference and guidance.

1. **Create Configuration File**: Create a file named `config.ini` in the `env/` folder with the following contents:

    ```ini
    [validator]
   name = [Desire Validator Name]
   keyfile = [Your comx key name]
   interval = [Weight Update Frequency (seconds)] #This is recommend to align with the subnet tempo 
   isTestnet = 0 #Whether using commune testnet: 1 means testnet; others means mainnet
    
    [api]
    url = [The trade services url] #For testnet: url = http://47.236.87.93:8000/  mainnet: url = http://8.219.104.233:8000/
    ```

2. Connect to the trade services

Each validator should connect to the trade services to obtain miner trades, this is used for evaluate miner's performance.

Set the [api] url parameters in config.ini file would be enough.

3. Register the validator & Stake

Note that you are required to register the validator first, this is because the validator has to be on the network in order to set weights. You can do this by running the following command:

```
comx module register <name> <your_commune_key> --netuid <OpenScope netuid>
```

OpenScope netuid: 5.

OpenScope Testnet netuid: 14.

You also need to stake on the subnet to be eligible for setting weights, you can do so by running the following command:

```bash
comx --testnet balance stake <key-name> <stake amount> <address> --netuid <netuid>
```



4. Serve the validator

```
python src/openscope/validator/validator.py
```

This will start a process that automatically performs all the validator duties.

You can set your own config file by --config your_config_name. The default config file is env/config.ini

Note: you need to keep this process alive, running in the background. 

The successful serve will show the following message:

```
...
Finished processing order, token_address: 0x6982508145454ce325ddbe47a25d4ec3d2311933
Finished processing order, token_address: 0x6982508145454ce325ddbe47a25d4ec3d2311933
5FCeSko1QPXqPj9yB3zQqcDpcgAxEg76XxJMS9T2Wmm283gt roi data: 1.5996246866748436
5FUFEK2UYiZv716XTHZrVaiJgkXo4HqXhK5YssweeRNohVpU roi data: 0.7172202893071074
5GQcQTQiWLCZHoTU6s9Wvv1o3ojgkNMte2VqyjDG9heXHEdH roi data: -0.6343400563799548
5CB63N3xeSJhDDn2oaamQQzZpX5t8GykJ5rdC6aQDKbzZLEU roi data: -0.14057561761578086
5Hb82dF3EAC9oSApNL3CQt4P86ndYKHQNAWNuTWAceWvS368 roi data: 2.746557003607876
weights for the following uids: [3, 4, 6, 5]
..
```

This shows that your validator is calculating the weights for miners based on the miner's position ROI conversion rule. You can still customize your own weight calculation logic but running the provide services is effortless and keep you aligned with the most validators.

This process will run every config.ini.interval seconds
