#!/usr/bin/env python

import argparse
import json
import logging
from types import SimpleNamespace
from embedder import create_edgelists, embed, post_embed, combine_embeddings, visualizer, most_similar

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('command',
                        choices=['create_edgelists', 'embed', 'post_embed', 'combine', 'visualise', 'most_similar'])
    parser.add_argument('-f', '--feature',
                        help='The feature on which compute the script. It subscribes the one in config.json')
    parser.add_argument('--reset', action='store_true',
                        help='Replace the previous embeddings instead of incrementing (only in combine mode)')
    parser.add_argument('--show', action='store_true',
                        help='Show the picture to video instead of saving to file (only in visualise mode)')

    parser.add_argument('-s', '--seed', nargs='?', default=None, help='The URI of the entity to be used as seed')
    parser.add_argument('-t', '--target', nargs='?', default=None, help='The URI of the entity to be used as target')
    parser.add_argument('-n', '--num_results', type=int, default=3, help='How many results are requested')

    parser.add_argument('-c', '--config', type=argparse.FileType('r'), default='config/config.json',
                        help='Path of configuration file.')

    return parser.parse_args()


def load_config(file):
    cfg = json.load(file)
    if type(cfg) == dict:
        cfg = SimpleNamespace(**cfg)

    return cfg


if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)

    config.feature = args.feature
    config.seed = args.seed
    config.target = args.target
    config.num_results = args.num_results
    config.reset = args.reset
    config.show = args.show

    try:

        if args.command == 'create_edgelists':
            create_edgelists.main(config)

        if args.command == 'embed':
            embed.main(config)
            post_embed.main(config)

        if args.command == 'post_embed':
            post_embed.main(config)

        if args.command == 'combine':
            combine = combine_embeddings.CombineEmbeddings(config)
            combine.run()

        if args.command == 'visualise':
            visualizer.main(config)

        if args.command == 'most_similar':
            ms = most_similar.MostSimilar(config)
            ms.find(args.seed, args.num_results)

    except RuntimeError as error:
        logger.error('[ERROR] %s' % error)
