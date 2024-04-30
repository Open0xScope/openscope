### Running A Validator

1. Create a file named config.ini in the env/ folder with the following contents (you can also see the sample as
   following):

```
[database]
host = your_host
port = your_port
name = default
user = user_name
password = password

[validator]
name = 1
keyfile = key
interval = 60

[api]
url = http://127.0.0.1/
```

2. Register the validator

Note that you are required to register the validator first, this is because the validator has to be on the network in
order to set weights. You can do this by running the following command:

```
comx module register <name> <your_commune_key> --netuid <0xscope netuid>
```

The current 0xscope netuid is 14.

3. Serve the validator

```
python src/openscope/validator/validator.py
```

Note: you need to keep this process alive, running in the background. Some options are nohup.
