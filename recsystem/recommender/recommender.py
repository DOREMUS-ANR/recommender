import codecs
import numpy as np
from scipy.spatial import distance as distance
import recommender.weights as weights
from werkzeug.contrib.cache import SimpleCache

cache = SimpleCache()

max_distance = 0


class Recommender:
    def __init__(self, etype, emb_dir, target=None):
        print('***** Init %s recommender *****' % etype)
        print('loading embeddings')
        self.vectors = np.genfromtxt('%s/%s.emb.v' % (emb_dir, etype))
        self.vectors = np.ma.array(self.vectors, mask=self.vectors < -1.)
        self.uris = np.array([line.strip() for line in codecs.open('%s/%s.emb.u' % (emb_dir, etype), 'r', 'utf-8')])
        self.pp_videos = np.array([line.strip() for line in codecs.open('resources/pp_video.txt', 'r', 'utf-8')])
        self.pp_videos_vec = np.ma.array([self.get_emb(uri) for uri in self.pp_videos])

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

    def recommend(self, seed, n=5, w=None, target='', focus=None):
        if n < 1:
            n = 5

        if w is None:
            w = weights.get(self.etype, target)
        elif len(w) == 6:  # artist sliders
            if np.array_equal(w, np.ones_like(w)):
                w = weights.get(self.etype, target)
            else:
                w = np.array(
                    [w[0], w[0], w[0], w[1], w[2], w[2], w[2], w[3], w[3], w[3], w[4], w[4], w[4], w[5], w[5], w[5]])

        else:
            w = np.array(w)

        _seed = self.get_emb(seed)
        if _seed is None:
            raise ValueError('URI not recognised')

        cache_id = '|'.join([seed, ','.join(w.astype(np.str)), target, focus or ''])
        rv = cache.get(cache_id)
        if rv is not None:
            print('taking result from cache')
            return rv[:n]

        print('computing scores')
        vec = self.pp_videos_vec if target == 'pp' else self.vectors
        uris = self.pp_videos if target == 'pp' else self.uris

        pool = vec[uris != seed]
        pool_uris = uris[uris != seed]

        closer = True
        l = len(vec) + 1

        if focus == 'genre':
            pool = np.delete(pool, np.arange(9, l), axis=1)
            pool = np.delete(pool, np.arange(6), axis=1)
            _seed = np.delete(_seed, np.arange(9, l), axis=0)
            _seed = np.delete(_seed, np.arange(6), axis=0)
            w = np.ones_like(_seed)
        elif focus == 'period':
            pool = np.delete(pool, np.arange(12), axis=1)
            _seed = np.delete(_seed, np.arange(12), axis=0)
            w = np.ones_like(_seed)
        elif focus == 'casting':
            pool = np.delete(pool, np.arange(3, l), axis=1)
            _seed = np.delete(_seed, np.arange(3, l), axis=0)
            w = np.ones_like(_seed)
        elif focus == 'composer':
            pool = np.delete(pool, np.arange(6, l), axis=1)
            pool = np.delete(pool, np.arange(3), axis=1)
            _seed = np.delete(_seed, np.arange(6, l), axis=0)
            _seed = np.delete(_seed, np.arange(3), axis=0)
            w = np.ones_like(_seed)
        elif focus == 'surprise':
            closer = False

        scores = np.array([[self.similarity(_seed, x, w) for x in pool]])
        full = np.concatenate([pool_uris.reshape(len(pool_uris), 1), scores.transpose()], axis=1)

        # sort
        full_sorted = sorted(full, key=lambda _x: float(_x[1]), reverse=closer)
        most_similar = full_sorted[:max(20, n)]
        json = [{'uri': _a[0], 'score': float(_a[1])} for _a in most_similar]

        # save in cache
        cache.set(cache_id, json, timeout=24 * 60 * 60)

        return json[:n]

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
