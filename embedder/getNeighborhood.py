import os
import json
import entity2vec.node2vec as node2vec
from os import path

import numpy as np
from types import SimpleNamespace
import scipy.spatial.distance as dist

import networkx as nx


def main():
    global config
    init()

    embeddings_file = 'emb/mop.emb'
    words = []
    vectors = []
    full = []

    skip = True
    with open(embeddings_file, 'r') as f:
        for line in f:
            if skip:
                skip = False
                continue

            fields = line.split()
            word = fields[0]
            vector = np.fromiter((float(x) for x in fields[1:]),
                                 dtype=np.float)
            words.append(word)
            vectors.append(vector)
            full.append([word, vector.flatten()])

    matrix = np.array(vectors)

    pos = words.index('http://data.doremus.org/vocabulary/iaml/mop/wsa')

    full_sorted = sorted(full, key=lambda x: dist.cosine(matrix[pos], x[1]))

    print('\n'.join(f[0] for f in full_sorted[1:11]))


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
