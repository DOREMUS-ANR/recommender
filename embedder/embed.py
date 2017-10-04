import os
import json
import entity2vec.node2vec as node2vec
from os import path
from types import SimpleNamespace

import networkx as nx


def main():
    global config
    init()

    what = 'genre'

    print('loading edgelists...')
    G = nx.read_edgelist(path.join(config.edgelistDir, '%s.edgelist' % what), nodetype=str, create_using=nx.DiGraph())

    for edge in G.edges():
        G[edge[0]][edge[1]]['weight'] = .3

    # for eg in os.listdir(config.edgelistDir):
    for eg in ['expression.edgelist']:
        H = nx.read_edgelist(path.join(config.edgelistDir, eg), nodetype=str, create_using=nx.DiGraph())
        for edge in H.edges():
            H[edge[0]][edge[1]]['weight'] = 6

        G = nx.compose(G, H)
    # G = nx.read_edgelist(path.join(config.edgelistDir, 'mop.edgelist'), nodetype=str, create_using=nx.DiGraph())

    G = G.to_undirected()

    directed = False
    preprocessing = False
    weighted = False
    p = 1
    q = 1
    walk_length = 4
    num_walks = 5
    dimensions = 80
    window_size = 8
    workers = 3
    iter = 5

    node2vec_graph = node2vec.Node2Vec(directed, preprocessing, weighted, p, q, walk_length,
                                       num_walks, dimensions, window_size, workers, iter)

    node2vec_graph.G = G

    node2vec_graph.learn_embeddings('emb/%s.emb' % what)


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
