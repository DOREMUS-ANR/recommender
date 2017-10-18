import codecs
import config as cs
import numpy as np
from scipy.spatial import distance
from .config import config

max_distance = 0


def main():
    if config.seed is None:
        raise RuntimeError('The seed "-s" has not been specified')

    f = config.chosenFeature
    print("Seed: %s" % config.seed)
    print("Type: %s" % f)

    find(config.seed, f)


def find(seed, ftype='artist', n=config.num_results):
    global max_distance

    if n < 1:
        n = config.num_results

    vectors = np.genfromtxt('%s/%s.emb.v' % (config.embDir, ftype))
    uris = np.array([line.strip() for line in codecs.open('%s/%s.emb.u' % (config.embDir, ftype), 'r', 'utf-8')])
    full = np.column_stack((uris, vectors))

    pos = np.where(uris == seed)[0][0]
    _seed = vectors[pos]

    # pos = np.where(uris == 'http://data.doremus.org/artist/269cec9d-5025-3a8a-b2ef-4f7acb088f2b')[0][0]
    # target = vectors[pos]

    full_len = len(full[0])

    max_distance = distance.sqeuclidean(np.ones(len(_seed)), np.ones(len(_seed)) * -1)

    scores = np.array([[compute_similarity(_seed, x[1:].astype(float)) for x in full]])
    full = np.concatenate([full, scores.transpose()], axis=1)

    # remove the seed from the list
    full = np.delete(full, pos, 0)

    # sort
    full_sorted = sorted(full, key=lambda _x: float(_x[full_len]), reverse=True)

    most_similar = full_sorted[:n]
    print('\n'.join('%s %s' % (f[0], f[full_len]) for f in most_similar))

    return [{'uri': _a[0], 'score': _a[full_len]} for _a in most_similar]


def compute_similarity(seed, target):
    b1 = np.where(seed < -1)[0]
    b2 = np.where(target < -1)[0]
    bad_pos = np.unique(np.concatenate([b1, b2]))

    _seed = np.delete(seed, bad_pos, axis=0)
    _target = np.delete(target, bad_pos, axis=0)

    if len(_seed) == 0:
        return 0

    # distance
    d = distance.sqeuclidean(_seed, _target)

    # how much info I am not finding
    penalty = len([x for x in b2 if x not in b1]) / len(seed)

    # score
    s = (max_distance - d) / max_distance
    return s * (1 - penalty)


if __name__ == '__main__':
    cs.parse_args()
    main()
