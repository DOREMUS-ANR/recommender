import os
import json
from os import path
from types import SimpleNamespace

import networkx as nx


def main():
    global config
    init()

    print('loading edgelists...')
    G = nx.Graph()
    for eg in os.listdir(config.edgelistDir):
        H = nx.read_edgelist(path.join(config.edgelistDir, eg), nodetype=str, create_using=nx.DiGraph())
        G = nx.compose(G, H)

    a = 'http://data.doremus.org/artist/b82c0771-5280-39af-ad2e-8ace2f4ebda3'  # verdi
    b = 'http://data.doremus.org/artist/32c2b0ff-35f1-3e65-b0ca-34aaf35f3d50'  # rossini

    print('computing shortest path')
    paths = nx.all_shortest_paths(G, a, b)
    print('done')
    print([p for p in paths])


def init():
    global sparql
    global config

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    if type(config) == dict:
        config = SimpleNamespace(**config)

    if not os.path.exists(config.edgelistDir):
        os.makedirs(config.edgelistDir)


if __name__ == '__main__':
    main()
