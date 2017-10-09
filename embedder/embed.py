import os
import entity2vec.node2vec as node2vec
from os import path
import networkx as nx

import config as cs
from config import config


def main():
    what = config.chosenFeature

    print('loading edgelists...')
    G = nx.read_edgelist(path.join(config.edgelistDir, '%s.edgelist' % what), nodetype=str, create_using=nx.DiGraph())

    for edge in G.edges():
        G[edge[0]][edge[1]]['weight'] = .3

    if what in config.features:
        feat = config.features[what]
        if 'dependencies' in feat:
            dependencies = feat['dependencies']

            for eg in dependencies:
                H = nx.read_edgelist(path.join(config.edgelistDir, eg), nodetype=str, create_using=nx.DiGraph())
                for edge in H.edges():
                    H[edge[0]][edge[1]]['weight'] = 6

                G = nx.compose(G, H)

    G = G.to_undirected()

    directed = False
    preprocessing = False
    weighted = False
    p = 1
    q = 1
    walk_length = 4
    num_walks = 3
    dimensions = 10
    window_size = 3
    workers = 3
    iter = 3

    node2vec_graph = node2vec.Node2Vec(directed, preprocessing, weighted, p, q, walk_length,
                                       num_walks, dimensions, window_size, workers, iter)

    node2vec_graph.G = G

    node2vec_graph.learn_embeddings('emb/%s.emb' % what)


def init():
    if not os.path.exists(config.edgelistDir):
        os.makedirs(config.edgelistDir)


if __name__ == '__main__':
    cs.parse_args()
    main()
