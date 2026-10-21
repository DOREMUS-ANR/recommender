import codecs
import numpy as np
from gensim.models import KeyedVectors
from scipy.spatial import distance as distance
from werkzeug.contrib.cache import SimpleCache
from recommender.utils import loadHeader

cache = SimpleCache()


def weighted_euclidean(a, b, w=None):
    # weighted squared euclidean distance
    return distance.minkowski(a, b, p=2, w=w)

# one tuple of embedding group labels per UI slider, in ?w= wire order
SLIDER_GROUPS = (
    ('mop',),
    ('birth_date', 'death_date'),
    ('casting',),
    ('function',),
    ('genre',),
    ('key',),
)


class Recommender:
    def __init__(self, f, emb_dir, weights_manager):
        print('***** Init %s recommender *****' % f)
        print('loading embeddings')

        self.embedding = KeyedVectors.load_word2vec_format('%s/%s.emb' % (emb_dir, f))
        self.uris = np.array(self.embedding.index2entity)
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

    def expand_slider_weights(self, sliders, target='default'):
        # groups without a slider keep the configured default weight
        length = len(self.vectors[0])
        w = np.array(self.weights_manager.get(self.etype, length=length, target=target), dtype=float)
        if len(w) != length:
            w = np.ones(length)
        weight_by_group = {label: sliders[i] for i, groups in enumerate(SLIDER_GROUPS) for label in groups}
        for i, label in enumerate(self.header):
            if i < length and label in weight_by_group:
                w[i] = weight_by_group[label]
        return w

    def resolve_weights(self, w, target='default'):
        length = len(self.vectors[0])
        if w is None:
            w = self.weights_manager.get(self.etype, length=length, target=target)
        else:
            w = np.array(w)
            if len(w) == 1:  # flat
                w = np.ones(length)
            elif len(w) == 6:  # artist sliders
                if np.array_equal(w, np.ones_like(w)):
                    w = self.weights_manager.get(self.etype, length=length, target=target)
                else:
                    w = self.expand_slider_weights(w, target)
        if len(w) != length:
            print('weight/vector length mismatch (%s vs %s), using default weights'
                  % (len(w), length))
            w = self.weights_manager.get(self.etype, length=length, target=target)
        return w

    def _scores_vectorized(self, seed, pool, w, max_distance):
        pool_filled = np.ma.filled(pool, 0.0)
        pool_mask = np.ma.getmaskarray(pool)
        seed_filled = np.ma.filled(seed, 0.0)
        seed_mask = np.ma.getmaskarray(seed)
        union = pool_mask | seed_mask
        diff = np.where(union, 0.0, pool_filled - seed_filled)
        dist = np.sqrt((diff ** 2 * w).sum(axis=1))
        penalty = (pool_mask & ~seed_mask).sum(axis=1) / len(seed)
        scores = (max_distance - dist) / max_distance * (1 - penalty)
        return np.where((~union).sum(axis=1) == 0, 0.0, scores)

    def recommend(self, seed, n=5, w=None, target='default', focus=None):
        if n < 1:
            n = 5

        w = self.resolve_weights(w, target=target)

        print(w)
        _seed = self.get_emb(seed)
        if _seed is None:
            raise ValueError('URI not recognised')

        _ones = np.ones_like(self.vectors[0])
        max_distance = weighted_euclidean(_ones, -_ones, w)

        cache_id = '|'.join([seed, ','.join(w.astype(np.str)), target, focus or ''])
        print(cache_id)
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

        scores = self._scores_vectorized(_seed, pool, w, max_distance)

        order = np.argsort(-scores if closer else scores, kind='stable')
        most_similar = order[:max(100, n)]
        json = [RecResult(pool_uris[i], scores[i], self.get_emb(pool_uris[i]), _seed) for i in most_similar]
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
