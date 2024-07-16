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

These trades is based on 20 different cryptocurrencies (token) right now, and there will be more!

Here is the list of the tokens we supported right now, we will use aggregated price to evaluate the price change instead of use a certain trading pair:

| Symbol  | Name      |
|---------|-----------|
| BTC   | Bitcoin |
| ETH    | Ethereum |
| ARB    | Arbitrum |
| OP    | Optimism |
| ONDO   | Ondo Finance |
| APE    | Ape |
| BLUR    | Blur |
| AAVE    | Aave |
| LDO    | Lido |
| SNX    | Synthtix |
| UNI     | Uniswap   |
| PEPE    | PEPE      |
| FET     | FET       |
| Pendle  | PENDLE    |
| SSV     | SSV       |
| ARKM    | Arkham    |
| ENS     | ENS       |
| Auction | Bounce    |
| ENA     | Ethena     |


Miners can open positions (open) and close positions (close) based on these tokens.

Opening a position can be either going long (1) or going short (-1).

You can use leverage to control your exposures, open a position with 1x leverage means you used your whole position value to long/short this token.

For each trade, we will take a certain amount of fees to prevent super high-frequency trading.

The fees are as follows:

- BTC/ETH: 0.05% 
- Other Token: 0.1% * Leverage

#### How do your trades affect positions' value & returns:

Let's say there are 20 token pairs right now and assume everybody’s initial position value is $20. 

Open a BTC long 1x is basically using $20 to long BTC 
Open another ETH long 1x means I use $20 to long ETH 

Now I'm using $40 which means my current leverage is 2x. 

If ETH goes up by 5% and BTC goes down by 2%:

My current position value is now 20+(20*0.05+20*(-0.02)) = 20.6

My return now is 20.6/20 = 3%

This also means my max total leverage (in terms of the whole account) can do is (maxleverage_bypair)*pair_mount

#### Use the OpenSource Dataset to train your strategy

Miner will need to constantly update the positions ([send the trades](/doc/Miner.md#run-the-miner)) and these trades should be based on the live token events.

Miners should also check:

[Event Rules](https://huggingface.co/datasets/0xscope/event_rules)

OpenScope will provide a complete history token events when you first sign up for being a miner. These events are the training dataset for miner's event-driving trading model.

You can also check more comprehensive history event data to train your model!

We have already open sourced all the events training data on our huggingface space:

[Event Trading Dataset](https://huggingface.co/datasets/0xscope/web3-trading-analysis)


#### Base Miner Examples:

If you want to start the miner first before you have a working strategy model, or you just want to run the miner with easy mode.

The miner example we provide can help you with than, once you serve the miner, it will run a very basic strategy that send 3 trades (random token, random action, 0.1 leverage) each time you run it (we call it IQ50 miner).

Just follow the [guide](../openscope/doc/Miner.md) and you will have a fully functional miner on the OpenScope subnet.

Notice:

The strategy is completely random so your score is fully random too. We wish the best luck of you but suggest you have a stable strategy once you know how everything works. 

### Join as a validator

#### Validator Scoring

Validators query trades from our trade services and use these trades and the positions to calculate a score for each miner.

The score is super simple:

Validators collect all your history position data to calculate the [serenity ratio](https://www.keyquant.com/Download/GetFile?Filename=%5CPublications%5CKeyQuant_WhitePaper_APT_Part1.pdf), an advance investment strategy risk & performance measurement indicator.


On top of this, validator apply penalties to your serenity score. The penalties are based on your max drawdown, the higher your drawdown, the lower your score.

#### Score to Weight

The rank will totally based on the score.

The weights will based on the rank.

The rank will be based on the following levels:

- Top 3 25% of the weights
- Top 4- Top 10  25% of the weights
- Top 10 - Top 25 25% of the weights
- Top 20 - Top 50 25% of the weights

If miners are on the same level, the weights for each miner will be based on the portion of their scores in the total scores, for example:

For the Top 3, their scores are 0.9 0.6 0.5

So for the top one, the weight share he will get is 0.9 / (0.9+0.6+0.5) = 45%

#### Eliminations (Not Available yet)

Elimination: The miner is marked as "eliminated" and will not receive weights until he gets de-registered and reg again

*Not active Elimination*:

If miner meet one of the following criteria after immune period:

Have <=1 trades
Have <1 position

*Copy-trading elimination*: (Metric Checkpoint)

If 2 miners are found to have same trade for the past 7 days, the miners later registered will be kicked out. Only the earliest miner will stay in the subnet if multiple miners are detected.

*Bad Performance Elimination*:

If the miner's position returns after the immune period is found to be lower than -50% for 2 straight days or accumulated 5 days.


*Liquidation Elimination*:

If a miner’s position return is found to be under -95% for one time by each validator interval, it will be eliminated. This is to simulate the liquidation under high leverage. Due to the crypto pair’s high volatility, with high leverage miner’s position return can change very fast.

*MDD Elimination*

The max drawdown we allow is 25%, which means if your drawdown is higher than 25%, your miner will be eliminated.

#### Run the validator

All of the tasks and calculation is written in the validator examples, once you start the process, it will help you do everything from querying the trades, calculating performance scores and set the weights.

You can also set the weights manually but we won't suggest that because you want to be align with other validators based on Yuma consensus to get fair dividends

Learn the details:

[Running A Validator](/doc/Validator.md)


