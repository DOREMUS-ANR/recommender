import codecs
import numpy as np
from gensim.models import KeyedVectors
from scipy.spatial import distance as distance
from werkzeug.contrib.cache import SimpleCache
from recommender.utils import loadHeader

cache = SimpleCache()

_ones = np.ones_like(100)


def weighted_euclidean(a, b, w=None):
    # weighted squared euclidean distance
    return distance.minkowski(a, b, p=2, w=w)


DEFAULT_DISTANCE = weighted_euclidean(_ones, -_ones)


class Recommender:
    def __init__(self, f, emb_dir, weights_manager):
        print('***** Init %s recommender *****' % f)
        print('loading embeddings')

        self.embedding = KeyedVectors.load_word2vec_format('%s/%s.emb' % (emb_dir, f))
        self.uris = np.array(self.embedding.index2entity)[0:1000]
        self.vectors = np.array([self.embedding.get_vector(k) for k in self.uris])
        self.vectors = np.ma.array(self.vectors, mask=-1. > self.vectors)

        self.pp_videos = np.array([line.strip() for line in codecs.open('resources/pp_video.txt', 'r', 'utf-8')])
        self.pp_videos_vec = np.ma.array([self.get_emb(uri) for uri in self.pp_videos])

        self.etype = f
        self.weights_manager = weights_manager
        self.header = loadHeader(f, emb_dir)

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
            w = self.weights_manager.get(self.etype, length=len(self.vectors[0]), target=target)
        elif len(w) == 6:  # artist sliders
            if np.array_equal(w, np.ones_like(w)):
                w = self.weights_manager.get(self.etype, length=len(self.vectors[0]), target=target)
            else:
                w = np.array(
                    [w[0], w[0], w[0], w[1], w[1], w[2], w[2], w[2], w[3], w[3], w[3], w[4], w[4], w[4], w[5], w[5],
                     w[5]])
        else:
            w = np.array(w)

        _seed = self.get_emb(seed)
        if _seed is None:
            raise ValueError('URI not recognised')

        _ones = np.ones_like(self.vectors[0])
        max_distance = weighted_euclidean(_ones, -_ones, w)

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

        if focus == 'surprise':
            closer = False
        elif focus is not None:
            pool, _seed, w = self.cropOn(focus, pool, _seed, w)

        scores = np.array([[self.similarity(_seed, x, w, max_distance) for x in pool]])
        full = np.concatenate([pool_uris.reshape(len(pool_uris), 1), scores.transpose()], axis=1)

        # sort
        full_sorted = sorted(full, key=lambda _x: float(_x[1]), reverse=closer)
        most_similar = full_sorted[:max(100, n)]
        json = [RecResult(_a[0], _a[1], self.get_emb(_a[0]), _seed) for _a in most_similar]
        # save in cache
        cache.set(cache_id, json, timeout=24 * 60 * 60)

        return json[:n]

    def cropOn(self, focus, pool, seed, w):
        if focus == 'period':
            focus = 'composition_date'
        elif focus == 'casting':
            focus = 'solo'

        pos = np.argwhere(self.header == focus).flatten()
        pool = np.ma.array(pool)[:, pos]
        seed = seed[pos]
        w = w[pos]

        return pool, seed, w

    @staticmethod
    def similarity(seed, target, w=None, max_distance=DEFAULT_DISTANCE):
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
        s = (max_distance - d) / max_distance
        return s * (1 - penalty)


class RecResult:
    def __init__(self, uri, score, target, seed):
        self.uri = uri
        self.score = float(score)
        self.target = target
        self.seed = seed
        self.explain = None

    def toJson(self):
        x = {'uri': self.uri, 'score': self.score}
        if self.explain is not None:
            x['explain'] = self.explain
        return x
