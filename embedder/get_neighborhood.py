import codecs

import config as cs
import numpy as np
from scipy.spatial import distance
from config import config


def main():
    if config.seed is None:
        raise RuntimeError('The seed "-s" has not been specified')

    f = config.chosenFeature
    print("Seed: %s" % config.seed)
    print("Type: %s" % f)

    vectors = np.genfromtxt('emb/%s.emb.v' % config.chosenFeature)
    uris = np.array([line.strip() for line in codecs.open('emb/%s.emb.u' % f, 'r', 'utf-8')])
    full = np.column_stack((uris, vectors))

    pos = np.where(uris == config.seed)[0][0]
    seed = vectors[pos]

    full_len = len(full[0])

    print(full_len)

    scores = np.array([[compute_score(seed, x[1:].astype(float)) for x in full]])
    full = np.concatenate([full, scores.transpose()], axis=1)

    full_sorted = sorted(full, key=lambda _x: float(_x[full_len]))
    print('\n'.join('%s %s' % (f[0], f[full_len]) for f in full_sorted))


def compute_score(seed, target):
    b1 = np.where(seed < -1)[0]
    b2 = np.where(target < -1)[0]
    bad_pos = np.unique(np.concatenate([b1, b2]))

    _seed = np.delete(seed, bad_pos, axis=0)
    _target = np.delete(target, bad_pos, axis=0)

    # distance
    d = distance.euclidean(_seed, _target)
    # how much info I am not finding
    penalty = len([x for x in b2 if x not in b1]) / len(seed)

    return d * (1 - penalty)


if __name__ == '__main__':
    cs.parse_args()
    main()
