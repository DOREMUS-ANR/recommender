import codecs

import config as cs
import numpy as np
from scipy import spatial as spatial
from recsystem.embedder.common.config import config

max_distance = 0


def main():
    if config.seed is None:
        raise RuntimeError('The seed "-s" has not been specified')

    f = config.chosenFeature
    print("Seed: %s" % config.seed)
    print("Type: %s" % f)

    find(config.seed, f, config.num_results)


def find(seed, ftype='artist', n=config.num_results, w=None):
    global max_distance

    if n < 1:
        n = config.num_results

    print('loading embeddings')
    vectors = np.genfromtxt('%s/%s.emb.v' % (config.embDir, ftype))
    uris = np.array([line.strip() for line in codecs.open('%s/%s.emb.u' % (config.embDir, ftype), 'r', 'utf-8')])
    # f_length = np.array([line.strip() for line in codecs.open('%s/%s.emb.h' % (config.embDir, ftype), 'r', 'utf-8')])
    # f_length = list(map(int, f_length[1].split()))

    pos = np.where(uris == seed)[0][0]
    _seed = vectors[pos]

    if w is None:
        w = np.ones(len(_seed))
        w = w / w.sum()
    else:
        w = np.array(w)
        if len(w) < len(_seed):
            temp = [np.ones(k, np.float32) * w[i] for i, k in enumerate([3, 2, 3, 3, 3, 3])]
            w = np.array([item for sublist in temp for item in sublist])

    max_distance = weightedL2(np.ones(len(_seed)), np.ones(len(_seed)) * -1, w)

    print('computing scores')
    scores = np.array([[compute_similarity(_seed, x.astype(float), w) for x in vectors]])
    full = np.concatenate([uris.reshape(len(uris), 1), scores.transpose()], axis=1)

    # remove the seed from the list
    full = np.delete(full, pos, 0)

    # sort
    full_sorted = sorted(full, key=lambda _x: float(_x[1]), reverse=True)
    most_similar = full_sorted[:n]
    print('\n'.join('%s %s' % (f[0], f[1]) for f in most_similar))

    return [{'uri': _a[0], 'score': _a[1]} for _a in most_similar]


def compute_similarity(seed, target, w):
    b1 = np.where(seed < -1)[0]
    b2 = np.where(target < -1)[0]
    bad_pos = np.unique(np.concatenate([b1, b2]))

    _seed = np.delete(seed, bad_pos, axis=0)
    _target = np.delete(target, bad_pos, axis=0)
    _w = np.delete(w, bad_pos, axis=0)

    if len(_seed) == 0:
        return 0

    # distance
    d = weightedL2(_seed, _target, _w)

    # how much info I am not finding
    penalty = len([x for x in b2 if x not in b1]) / len(seed)

    # score
    s = (max_distance - d) / max_distance
    return s * (1 - penalty)


def weightedL2(a, b, w=1):
    return spatial.distance.minkowski(a, b, w=w)
    # return spatial.distance.cosine(a, b)


if __name__ == '__main__':
    cs.parse_args()
    main()
