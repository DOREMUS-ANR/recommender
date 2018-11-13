import os
import entity2vec.node2vec as node2vec
from os import path
import networkx as nx


def main(config):
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
                H = nx.read_edgelist(path.join(config.edgelistDir, '%s.edgelist' % eg), nodetype=str,
                                     create_using=nx.DiGraph())
                for edge in H.edges():
                    H[edge[0]][edge[1]]['weight'] = 6

                G = nx.compose(G, H)

    G = G.to_undirected()

    n2vOpt = config.node2vec
    directed = n2vOpt["directed"]
    preprocessing = n2vOpt["preprocessing"]
    weighted = n2vOpt["weighted"]
    p = n2vOpt["p"]
    q = n2vOpt["q"]
    walk_length = n2vOpt["walk_length"]
    num_walks = n2vOpt["num_walks"]
    dimensions = n2vOpt["dimensions"]
    window_size = n2vOpt["window_size"]
    workers = n2vOpt["workers"]
    iter = n2vOpt["iter"]

    print(n2vOpt)

    node2vec_graph = node2vec.Node2Vec(directed, preprocessing, weighted, p, q, walk_length,
                                       num_walks, dimensions, window_size, workers, iter)

    node2vec_graph.G = G

    node2vec_graph.learn_embeddings('%s/%s.emb' % (config.embDir, what), 'text')


def init(config):
    if not os.path.exists(config.edgelistDir):
        os.makedirs(config.edgelistDir)
