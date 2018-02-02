import argparse
import json
from types import SimpleNamespace

with open('../config/config.json') as json_data_file:
    config = json.load(json_data_file)

if type(config) == dict:
    config = SimpleNamespace(**config)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cf', "--chosenFeature", default=config.chosenFeature,
                        help="The feature on which compute the script. It subscribes the one in config.json")

    parser.add_argument('-s', "--seed", nargs='?', default=None, help="The URI of the entity to be used as seed")
    parser.add_argument('-t', "--target", nargs='?', default=None, help="The URI of the entity to be used as target")
    parser.add_argument('-n', "--num_results", type=int, default=3, help="How many results are requested")

    args = parser.parse_args()

    config.chosenFeature = args.chosenFeature
    config.seed = args.seed
    config.target = args.target
    config.num_results = args.num_results
