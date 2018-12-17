import collections
import numpy as np
from SPARQLWrapper import SPARQLWrapper

from recommender.utils import loadHeader

sparql = SPARQLWrapper('http://data.doremus.org/sparql')


class Explainator:
    def __init__(self, entity_type, uri, vector, weights, config):
        self.seed_uri = uri
        self.seed_vector = vector

        if weights is None:
            self.weights = np.ones_like(vector)
        else:
            self.weights = np.array(weights)

        self.type = entity_type
        self.header = loadHeader(entity_type, config.embDir)

    def explain(self, target):
        target_uri = target.uri
        target_vector = target.target

        _seed = self.seed_vector
        _target = target_vector
        _w = self.weights

        # print(_seed)
        # print(_target)
        pairwise_diff = (_seed - _target) * _w

        target.explain = self.get_best_dimensions(pairwise_diff)
        return target.explain

    def get_best_dimensions(self, pairwise_diff):
        # print(pairwise_diff)
        pd = np.absolute(pairwise_diff.filled())
        pd = 2 - pd

        named_diff = [(self.header[i], pd[i]) for i in np.arange(0, len(pd))]

        reduced = collections.defaultdict(int)
        for a, b in named_diff:
            if a == 'bd' or a == 'dd':
                reduced['period_old'] += b / 4
            else:
                if a in ['birth_place', 'death_place']:
                    a = 'places'
                    b /= 2
                if a in ['birth_date', 'death_date']:
                    a = 'period'
                    b /= 2
                reduced[a] += b / 10

        largest = sorted(reduced.items(), key=lambda e: -e[1])
        return largest[0:3]
