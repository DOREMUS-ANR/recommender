import numpy as np
from scipy import spatial as spatial
from gensim.models import KeyedVectors

max_distance = 0


class MostSimilar:
    def __init__(self, args):
        self.emb_dir = args.embDir
        f = args.feature
        if f is None:
            raise RuntimeError('You must specify the feature using -f or --feature')

        self.feature = f

        print('loading embeddings')
        self.embedding = KeyedVectors.load_word2vec_format('%s/%s.emb' % (self.emb_dir, f))
        self.uris = self.embedding.index2entity
        self.vectors = [self.embedding.get_vector(k) for k in self.uris]

        self.max_distance = 0

    def find(self, seed, n=5, w=None):
        if seed is None:
            raise RuntimeError('The seed "-s" has not been specified')

        print("Seed: %s" % seed)

        if n < 1:
            n = 5

        if self.feature in ['artist', 'expression']:
            return self.find_complex(seed, n, w)
        else:
            return self.find_base(seed, n)

    def find_base(self, seed, n):
        print(n)
        sm = self.embedding.most_similar(positive=[seed], topn=n)
        print(sm)
        return sm

    def find_complex(self, seed, n, w):
        pos = np.where(self.uris == seed)[0][0]
        _seed = self.vectors[pos]

        if w is None:
            w = np.ones(len(_seed))
            w = w / w.sum()
        else:
            w = np.array(w)
            if len(w) < len(_seed):
                temp = [np.ones(k, np.float32) * w[i] for i, k in enumerate([3, 2, 3, 3, 3, 3])]
                w = np.array([item for sublist in temp for item in sublist])

        if self.max_distance == 0:
            self.max_distance = weighted_l2(np.ones(len(_seed)), np.ones(len(_seed)) * -1, w)

        print('computing scores')
        scores = np.array([[self.compute_similarity(_seed, x.astype(float), w) for x in self.vectors]])
        full = np.concatenate([self.uris.reshape(len(self.uris), 1), scores.transpose()], axis=1)

        # remove the seed from the list
        full = np.delete(full, pos, 0)

        # sort
        full_sorted = sorted(full, key=lambda _x: float(_x[1]), reverse=True)
        most_similar = full_sorted[:n]
        print('\n'.join('%s %s' % (f[0], f[1]) for f in most_similar))

        return [{'uri': _a[0], 'score': _a[1]} for _a in most_similar]

    def compute_similarity(self, seed, target, w):
        b1 = np.where(seed < -1)[0]
        b2 = np.where(target < -1)[0]
        bad_pos = np.unique(np.concatenate([b1, b2]))

        _seed = np.delete(seed, bad_pos, axis=0)
        _target = np.delete(target, bad_pos, axis=0)
        _w = np.delete(w, bad_pos, axis=0)

        if len(_seed) == 0:
            return 0

        # distance
        d = weighted_l2(_seed, _target, _w)

        # how much info I am not finding
        penalty = len([x for x in b2 if x not in b1]) / len(seed)

        # score
        s = (self.max_distance - d) / self.max_distance
        return s * (1 - penalty)


def weighted_l2(a, b, w=1):
    return spatial.distance.minkowski(a, b, w=w)
    # return spatial.distance.cosine(a, b)
