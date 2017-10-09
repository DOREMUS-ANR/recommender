import json
import argparse
from types import SimpleNamespace

with open('config.json') as json_data_file:
    config = json.load(json_data_file)

if type(config) == dict:
    config = SimpleNamespace(**config)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cf', "--chosenFeature",
                        help="The feature on which compute the script. It subscribes the one in config.json")

    args = parser.parse_args()
    if 'chosenFeature' in args:
        config.chosenFeature = args.chosenFeature