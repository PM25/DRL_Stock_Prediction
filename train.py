from mylib.agent import Agent
from mylib import data

import sys
import numpy as np
import argparse
import json
import os

parser = argparse.ArgumentParser(description="Portfolio Management Model Training")
parser.add_argument("--train", "-t", type=str, help="Path to stock training data.")
parser.add_argument("--window", "-w", type=int, help="Window Size.")
parser.add_argument("--episode", "-e", type=int, help="Episode Size.")
parser.add_argument("--model", "-m", type=str, help="Model Name.")
args = parser.parse_args()

# Default Data
if (args.train == None): args.train = "data/train/2002.TW.csv"
if (args.window == None): args.window = 10
if (args.episode == None): args.episode = 1000
if (args.model == None):
    if(not os.path.isfile("models/metadata.json")):
        start_episode = 1
        stockdata = data.StockData(args.train)
        agent = Agent(args.window)
    else:
        with open("models/metadata.json", 'r') as in_file:
            metadata = json.load(in_file)
        agent = Agent(args.window, metadata["model"])
        std = np.array(metadata["std"])
        mean = np.array(metadata["mean"])
        start_episode = metadata["episode"]
        stockdata = data.StockData(args.train, mean, std)

stock_data = stockdata.raw_data
mean = stockdata.mean
std = stockdata.std
out_data = {}
out_data["std"] = list(std)
out_data["mean"] = list(mean)
end_episode = start_episode + args.episode + 1


for episode_step in range(start_episode, end_episode):
    state = stockdata.get_state(0, args.window)

    buy_count = 0
    sell_count = 0
    for sample_step in range(1, stockdata.sample_size):
        reward = agent.money - agent.base_money
        done = True if (sample_step != stockdata.sample_size - 1) else False
        next_state = stockdata.get_state(sample_step, args.window)
        close_price = float(stockdata.raw_data[sample_step][1])

        action = agent.choose_action(state, 0)
        if (action == 0):  # Sit
            pass
        elif (action == 1):  # Buy
            money = agent.buy(close_price)
            if (money != False):
                reward = money - agent.base_money
                buy_count += 1
        elif (action == 2):  # Sell
            money = agent.sell(close_price)
            if (money != False):
                reward = money - agent.base_money
                sell_count += 1
        agent.deep_q_learning(state, reward, action, next_state, done)
    print("BUY", buy_count, ", SELL", sell_count)
    print("Total Reward", reward)
    agent.reset()
    if (episode_step % 10 == 0):
        agent.save_model("episode_{}".format(episode_step))

        out_data["model"] = "episode_{}".format(episode_step)
        out_data["episode"] = episode_step
        out_data["std"] = list(std)
        out_data["mean"] = list(mean)
        with open("models/metadata.json", 'w') as out_file:
            json.dump(out_data, out_file, ensure_ascii=False, indent=4)
