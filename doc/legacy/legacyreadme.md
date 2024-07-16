# OpenScope

Welcome to OpenScope Subnet, where the power of decentralized AI converges with the world of cryptocurrency trading. OpenScope is a revolutionary network that leverages 0xScope's comprehensive cryptocurrency event dataset to train advanced AI models for predicting price movements with unprecedented accuracy.

![frontpage](/doc/assets/frontpage.png)


## Table of Contents

- [OpenScope](#openscope)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Motivation](#Unleashing-the-Power-of-Decentralized-AI-for-Crypto-Trading-with-OpenScope)
  - [Running A Miner](#running-a-miner)
  - [Running A Validator](#running-a-validator)
  <!--
  - [Running A Validator](#running-a-validator)
  - [Launcher Script](#launcher-script)
    - [Using the launcher](#using-the-launcher)
    - [What it does](#what-it-does)
    - [Video tutorial](#video-tutorial)
   -->

## Overview

Visit [OpenScope Website](https://open.0xscope.com/)

In the fast-paced world of cryptocurrency, staying ahead of the game is crucial. Introducing OpenScope, a groundbreaking decentralized AI network that revolutionizes crypto trading like never before.

OpenScope harnesses the power of 0xScope's comprehensive cryptocurrency event dataset to train cutting-edge, event-driven trading models. By leveraging a diverse range of on-chain data, technical analysis, and news events, such as exchange deposits/withdrawals, project collaborations, and influencer signals, OpenScope empowers miners to develop highly performant AI models that predict potential price movements with unparalleled accuracy.

## How OpenScope V2 works

The OpenScope Subnet will have 3 phase, with different miner tasks & validator tasks, right now we are in Phase 1.

### Phase 1

Phase 1 will be the beta version of OpenScope, as a cold start we want to OpenScope to be more friendly to participants, the requirements for miners and validators are less intense.

Miners are required to send cryptocurrency trades based on provided live token events.

This can do done by subscribe our live event feed.

These trades should be based on the AI trading model trained with the provided history token events.

We have already open sourced all the events training data on our huggingface space:

[Event Trading Dataset](https://huggingface.co/datasets/0xscope/web3-trading-analysis)

You can also read the descriptions about these data here:

[Event Rules](https://huggingface.co/datasets/0xscope/event_rules)

Validators will calculated each miner's performance score based on each miner's trades in each cycle.

In a nutshell, the scores will be based on:

1. Each miner's ROI
2. Each miner's win rate

A trade is considered "Win" if the return of this trade after 4 hours is positive.

Win rate is considered important because we expect the trades are based on these events, instead of other trading strategies.

These performances scores will used as each miner's performance to assign weights, the higher the value, the higher the weights.

These weights will eventually decide the incentive of each miner, to be specifically the commune token they gets.


### Phase 2

Start from Phase 2, we will officially full utilize the power of the commune network.

In Phase 1, miners are allowed to make trades manually.

Start from Phase 2, miners' trades should be directly becomes a model's output (events as the input), which means the miner scripts should have their own logic to process the events and convert the signals to trades, just like a general AI model.

Validators will still take trades and perform the usual tasks.

### Phase 3

In phase 3, miner's will be require to update their modules in each cycle and no longer need to send trades.

Validators will directly evaluate the module's performance through a set of standards. To be more detailed, validators will consider the miners' module as a general AI model, input events and expect to receive trades.

This will be the final form of the OpenScope Subnet.

## Motivation

OpenScope - Unleashing the Power of Decentralized AI for Crypto Trading with OpenScope

The network thrives on the symbiotic relationship between miners and validators. Miners utilize 0xScope's rich event data to train sophisticated AI models and generate trading orders based on real-time event inputs. Validators, on the other hand, continuously assess the performance of these models, assigning higher weights to the most successful miners. This dynamic interplay ensures that the best-performing models are consistently rewarded, driving innovation and excellence within the OpenScope ecosystem.

With OpenScope, you can tap into the collective intelligence of a decentralized network, where the brightest minds in AI and crypto converge to create trading strategies that adapt to the ever-evolving market landscape. Join the OpenScope revolution today and experience the future of crypto trading, powered by cutting-edge AI technology and the wisdom of the crowd.

## Prerequisite

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install CommuneX and cli

[Set up Commune](https://communeai.org/docs/installation/setup-commune)

### Get a CommuneX Key

[Key Basics](https://communeai.org/docs/working-with-keys/key-basics)

## Be part of the OpenScope

There are essentially 2 ways to participant in OpenScope, you can join as a miner, join as a validator, or you can be both!

### Join as a miner

You easily run the miner services in minutes following the tutorials we prepared for you:

[Running A Miner](/doc/Miner.md)

And of course, you have to understand what should a miner do.

#### What should a miner do

Basically, each miner's will have the ability to send "trades" to our trade services.

These trades is based on 10 different cryptocurrencies (token).

Here is the list of the tokens and their addresses:

| Symbol  | Name      | Chain | Address                                    |
|---------|-----------|-------|--------------------------------------------|
| LINK    | Chainlink | ETH   | 0x514910771af9ca656af840dff83e8264ecf986ca |
| UNI     | Uniswap   | ETH   | 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984 |
| PEPE    | PEPE      | ETH   | 0x6982508145454ce325ddbe47a25d4ec3d2311933 |
| FET     | FET       | ETH   | 0xaea46a60368a7bd060eec7df8cba43b7ef41ad85 |
| Pendle  | PENDLE    | ETH   | 0x808507121b80c02388fad14726482e061b8da827 |
| SSV     | SSV       | ETH   | 0x9d65ff81a3c488d585bbfb0bfe3c7707c7917f54 |
| ARKM    | Arkham    | ETH   | 0x6e2a43be0b1d33b726f0ca3b8de60b3482b8b050 |
| ENS     | ENS       | ETH   | 0xc18360217d8f7ab5e7c516566761ea12ce7f9d72 |
| Auction | Bounce    | ETH   | 0xa9b1eb5908cfc3cdf91f9b8b3a74108598009096 |
| ENA     | Ethena     | ETH   | 0x57e114b691db790c35207b2e685d4a43181e6061 |


Miners can open positions (open) and close positions (close) based on these tokens.

Each token is independent and all start with the same position size. This means each trading pair contributes to 10% of the total portfolio value at Genesis.

Opening a position can be either going long (1) or going short (-1) (Max 1X Leverage, basically spot but you can short). 

**Example:**

Let's say on Day 0, my total position value starts with 1 USD.

And I have 10 sub-accounts, each account has a 0.1 value (or USD).

And for each sub-account, you can only trade one specific token. 

On Day 0, I only created a $PEPE long position.

On Day 1, cause $PEPE is up 50%, my $PEPE sub-account is now worth 0.15.

As other sub-accounts stay no change (no open position).

My total position value is 1.05 USD, and my current ROI is 5%.

Miner will need to constantly update the positions ([send the trades](/doc/Miner.md#run-the-miner)) and these trades should be based on the live token events.

Miners should also check:

[Event Rules](https://huggingface.co/datasets/0xscope/event_rules)

OpenScope will provide a complete history token events when you first sign up for being a miner. These events are the training dataset for miner's event-driving trading model.

You can also check more comprehensive history event data to train your model!

We have already open sourced all the events training data on our huggingface space:

[Event Trading Dataset](https://huggingface.co/datasets/0xscope/web3-trading-analysis)


#### Base Miner Examples:

If you want to start the miner first before you have a working strategy model, or you just want to run the miner with easy mode.

The miner example we provide can help you with than, once you serve the miner, it will run a very basic strategy that send trades each day automatically (we call it IQ50 miner).

Just follow the [guide](../openscope/doc/Miner.md) and you will have a fully functional miner on the OpenScope subnet.

Notice:

The strategy is completely random so your performance score is fully random too. We wish the best luck of you but suggest you have a stable strategy once you know how everything works. 

### Join as a validator

Validators query trades from our trade services and use these trades to calculate the miners' performance score.

In a nutshell, the scores will be based on:

1. Each miner's Position ROI
2. Each miner's Trade Win Rate

A trade is considered "Win" if the return of this trade after 4 hours is positive.

All of the tasks and calculation is written in the validator examples, once you start the process, it will help you do everything from querying the trades, calculating performance scores and set the weights.

You can also set the weights manually but we won't suggest that because you want to be align with other validators based on Yuma consensus to get fair dividends

Learn the details:

[Running A Validator](/doc/Validator.md)


