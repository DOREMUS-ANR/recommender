import json
import numpy as np
import pylab as Plot
import codecs
from types import SimpleNamespace
from SPARQLWrapper import SPARQLWrapper, JSON

from config import config

XSD_NAMESPACE = 'http://www.w3.org/2001/XMLSchema#'

sparql = SPARQLWrapper(config.endpoint)
feat_len = {
    'default': 1
}


def get_embed(uri, emb):
    vectors = np.loadtxt('emb/%s.emb.v' % emb)
    feat_len[emb] = len(vectors[0])
    # labels = [line.strip() for line in codecs.open('emb/%s.emb.l' % config.chosenFeature, 'r', 'utf-8')]
    uris = np.array([line.strip() for line in codecs.open('emb/%s.emb.u' % emb, 'r', 'utf-8')])

    index = np.where(uris == uri)
    return vectors[index][0] if len(index[0]) else None


def to_embed(obj, emb):
    global XSD_NAMESPACE

    type = obj['type']
    value = obj['value']

    if type == 'uri':
        return get_embed(value, emb)

    if type == 'literal':
        v = value.replace(" ", '_')
        return None

    if type == 'typed-literal' and obj['datatype'].startswith(XSD_NAMESPACE):
        # is a date!
        # range mapping {-100,2016} -> {0,2} -> {-1,1}
        n = (int(value[:4]) / 1050) - 1
        return [n]

    return None


def get_partial_emb(f, uri):
    f = SimpleNamespace(**f)
    # print(f.label)

    # setup query
    query = "SELECT * where { %s }" % f.query.replace('?a', uri)

    # perform query
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    emb = getattr(f, 'embedding', None)

    all_embs = [to_embed(result['o'], emb) for result in results["results"]["bindings"]]
    all_embs = [x for x in all_embs if x is not None]

    if len(all_embs):
        feat_len[emb] = len(all_embs[0])
        return np.mean(all_embs, axis=0)
    else:
        return np.ones(feat_len.get(emb, 1)) * -2


def main():
    with open('artist-similarity.json') as json_data_file:
        feature_list = json.load(json_data_file)

    # giuseppeverdi = '<http://data.doremus.org/artist/b82c0771-5280-39af-ad2e-8ace2f4ebda3>'
    big_query = """select DISTINCT * where {
                  ?a a ecrm:E21_Person .
                  [] ecrm:P14_carried_out_by ?a .
                } ORDER BY (COUNT (*))
                LIMIT 10"""

    sparql.setQuery(big_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    artist_list = []
    for result in results["results"]["bindings"]:
        uri = "<%s>" % result['a']['value']
        print(uri)
        artist = flatten([get_partial_emb(f, uri) for f in feature_list])
        artist_list.append(artist)

    with open('emb/artist.emb.v', 'w') as f:
        for a in artist_list:
            nums = [str(n) for n in a]
            f.write(' '.join(nums))
            f.write('\n')

    with open('emb/artist.emb.h', 'w') as fu:
        fu.write(' '.join([ft['label'].replace(' ', '_') for ft in feature_list]))
        fu.write('\n')
        fu.write(' '.join([str(feat_len[ft.get('embedding', 'default')]) for ft in feature_list]))


def flatten(lst=None):
    if lst is None:
        lst = []

    return [item for sublist in lst for item in sublist]


if __name__ == '__main__':
    main()
