## Prerequisite

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


## Run the Validator

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

For now, subnet's 'minimum stake' is zero, but we require each validator to stake at least 1000 $COMAI token to be able to access the trade services.



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
5FqetfEViLWeiuZ3oLiX9ie6vbVh4Pcjqb9bAuPtR6wkWAWT roi data: 30.43249630436874, latest position_value: 13.043249630436874
5Dke7ytFLxnoSLwGz3tEx3XzLSu9SqHPkJLigSP2RK7E2hYe roi data: 8.882161741410197, latest position_value: 10.88821617414102
5Gbxze2jknTzFPNS3VgEUjkdXXzvwnrCWiz7waM5CcwzDSPF roi data: 30.235778720520447, latest position_value: 13.023577872052044
id: 5GKKY4d6CGqh2JhBZb64kjko2xwTsit8CxPHrn4wxMo1yncz, serenity: -4.857659777745586, mdd: -0.5686277362923495
id: 5HKUF75DZWNDM4K6zPb4AU3gfscJXFqNEhnnwo6t9tSG2YTQ, serenity: 0.010519085248333325, mdd: -0.3172992833869538
id: 5Dke7ytFLxnoSLwGz3tEx3XzLSu9SqHPkJLigSP2RK7E2hYe, serenity: 1.746331915903895, mdd: -0.2942847207539201
weights for the following uids: [3, 4, 6, 5]
..
```

This shows that your validator is calculating the weights for miners based on the miner's performance. You can still customize your own weight calculation logic but running the provide services is effortless and keep you aligned with the most validators.

This process will run every config.ini.interval seconds
