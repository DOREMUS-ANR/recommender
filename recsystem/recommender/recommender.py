import codecs
import numpy as np
from scipy.spatial import distance as distance
import recommender.weights as weights

max_distance = 0


class Recommender:
    def __init__(self, etype, emb_dir, target=None):
        print('***** Init %s recommender *****' % etype)
        print('loading embeddings')
        self.vectors = np.genfromtxt('%s/%s.emb.v' % (emb_dir, etype))
        self.vectors = np.ma.array(self.vectors, mask=self.vectors < -1.)
        self.uris = np.array([line.strip() for line in codecs.open('%s/%s.emb.u' % (emb_dir, etype), 'r', 'utf-8')])

        self.etype = etype
        self.weights = weights.get(etype, target)

        _ones = np.ones_like(self.vectors[0])
        self.max_distance = weighted_euclidean(_ones, -_ones, self.weights)

    def get_emb(self, uri):
        # uri to embedding
        v = self.vectors[self.uris == uri]
        if v.size == 0:
            return None
        return v[0]

    def recommend(self, seed, n=5, w=None, target=None):
        if n < 1:
            n = 5

        if w is not None:
            w = np.array(w)
        else:
            w = weights.get(self.etype, target)

        _seed = self.get_emb(seed)
        if _seed is None:
            raise ValueError('URI not recognised')

        print('computing scores')
        pool = self.vectors[self.uris != seed]
        pool_uris = self.uris[self.uris != seed]
        scores = np.array([[self.similarity(_seed, x, w) for x in pool]])
        full = np.concatenate([pool_uris.reshape(len(pool_uris), 1), scores.transpose()], axis=1)

        # sort
        full_sorted = sorted(full, key=lambda _x: float(_x[1]), reverse=True)
        most_similar = full_sorted[:n]

        return [{'uri': _a[0], 'score': _a[1]} for _a in most_similar]

    def similarity(self, seed, target, w=None):
        b1 = np.argwhere(seed.mask)
        b2 = np.argwhere(target.mask)
        bad_pos = np.unique(np.concatenate([b1, b2]))

        _seed = np.delete(seed, bad_pos, axis=0)
        _target = np.delete(target, bad_pos, axis=0)
        _w = np.delete(w, bad_pos, axis=0)

        if len(_seed) == 0:
            return 0

        # distance
        d = weighted_euclidean(_seed, _target, w=_w)

        # how much info I am not finding
        penalty = len([x for x in b2 if x not in b1]) / len(seed)

        # score
        s = (self.max_distance - d) / self.max_distance
        return s * (1 - penalty)


def weighted_euclidean(a, b, w=None):
    # weighted squared euclidean distance
    return distance.minkowski(a, b, p=2, w=w)
