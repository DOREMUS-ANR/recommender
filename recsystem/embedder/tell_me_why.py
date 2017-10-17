import json
import os
import config as cs
import numpy as np
from types import SimpleNamespace
from SPARQLWrapper import SPARQLWrapper, JSON
from scipy.spatial import distance

from .combine_embeddings import to_embed
from .config import config

sparql = SPARQLWrapper(config.endpoint)


def main(seed, target):
    if seed is None:
        raise RuntimeError('The seed "-s" has not been specified')
    if target is None:
        raise RuntimeError('The target "-t" has not been specified')

    f = config.chosenFeature
    print("Seed: %s" % seed)
    print("Target: %s" % target)
    # print("Type: %s" % f)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open('%s/artist-similarity.json' % dir_path) as json_data_file:
        feature_list = json.load(json_data_file)

    intersections = [get_partials_intersections(f, "<%s>" % seed, "<%s>" % target) for f in feature_list]
    intersections = [x for x in intersections if x is not None]

    groups = []
    for its in intersections:
        obj = next((x for x in groups if x['group'] == its['group']), None)
        if obj is None:
            groups.append(its)
            continue

        v1 = obj['selected'][0]
        v2 = its['selected'][0]

        start = min(v1['o'], v1['similar'])
        end = min(v2['o'], v2['similar'])
        label = '%s-%s' % (start, end)

        score = (v1['score'] + v2['score']) / 2

        obj['label'] = obj['group']
        obj['selected'] = [{'o': label, 'similar': label, 'score': score}]

    humans = np.unique([to_humans(x) for x in groups])
    print('\n'.join(humans))

    return groups


def to_humans(x):
    label = x['label']
    strings = []
    for s in x['selected']:
        s = SimpleNamespace(**s)
        pre = 'same' if s.score >= 1 else 'similar'
        value = s.o
        if pre == 'same':
            post = '(%s times)' % s.n if int(s.n) >= 1 else ''
        else:
            post = 'and %s (score: %s)' % (s.similar, s.score)
        strings.append("%s %s: %s %s" % (pre, label, value, post))
    return '\n'.join(strings)


def get_partials_intersections(f, uri1, uri2):
    f = SimpleNamespace(**f)
    # print(f.label)
    how_many = config.num_results
    v1 = get_feature_values(f, uri1)

    selected = []
    if len(v1) > 0:
        v2 = get_feature_values(f, uri2)
        if len(v2) > 0:
            # shared exact values
            for a in v1:
                for b in v2:
                    if a['o'] == b['o']:
                        if a['n'] > b['n']:
                            selected.append(b)
                        else:
                            selected.append(a)
                        selected[-1]['score'] = 1
                        selected[-1]['similar'] = selected[-1]['o']

            if len(selected) == 0:
                # similar values
                for a in v1:
                    for b in v2:
                        if a['e'] is None or b['e'] is None:
                            continue
                        d = distance.sqeuclidean(a['e'], b['e'])
                        s = 1 - d
                        if len(selected) < how_many or selected[2]['score'] < s:
                            x = a.copy()
                            x['score'] = s
                            x['similar'] = b['o']
                            selected.append(x)

    selected = sorted(selected, key=lambda _x: int(_x['n']) * _x['score'], reverse=True)

    if len(selected) == 0:
        return None

    return {
        'label': f.label,
        'group': f.group,
        'selected': selected[:how_many]
    }


def get_feature_values(f, uri):
    # setup query
    query = "SELECT ?o COUNT(?o) as ?n " \
            "where { %s }" \
            "GROUP BY ?o ORDER BY DESC(?n)" % f.query.replace('?a', uri)

    # perform query
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    emb = getattr(f, 'embedding', None)

    all_values = [{
        "o": result['o']['value'],
        "n": result['n']['value'],
        "e": to_embed(result['o'], emb)
    } for result in results["results"]["bindings"]]

    return all_values


if __name__ == '__main__':
    cs.parse_args()
    main(config.seed, config.target)
