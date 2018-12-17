import codecs
import numpy as np

# PP_WEIGHTS = np.array([8.67, .6, .6, 1, 1, 1, 14.9, .6, 5.88, .6, 5.07, 9.85, .6, .6, .6, 26.5])
# SPOTIFY_WEIGHTS = np.array([.6, 1.45, .6, 1, 1, 1, 4.15, 1.47, 1.37, .6, 5.5, .6, .6, .6, .6, 2.65])


header_cache = {}


class WeightsManager:
    def __init__(self, config):
        self.w = config.weights

    def get(self, etype, length, target='default'):
        if etype in self.w:
            t = self.w[etype]
            if target in t:
                return t[target]

        return np.ones(length)


def loadHeader(type, emb_dir):
    if type in header_cache:
        return header_cache[type]

    header_file = '%s/%s.emb.h' % (emb_dir, type)

    heads = np.array([line.strip() for line in codecs.open(header_file, 'r', 'utf-8')])

    # header for printing
    head_label = heads[0].split()
    head_val = heads[1].split()
    head_dim = []
    for i in range(0, len(head_val)):
        for j in range(0, int(head_val[i])):
            head_dim.append(head_label[i])
    header_cache[type] = head_dim
    return np.array(head_dim)
