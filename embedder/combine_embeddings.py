import json
import numpy as np
import os
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
        try:
            n = (int(value[:4]) / 1050) - 1
            return [n]
        except:
            return None

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


def count_emb_len(emb):
    vectors = np.loadtxt('emb/%s.emb.v' % emb)
    return len(vectors[0])


def main():
    with open('artist-similarity.json') as json_data_file:
        feature_list = json.load(json_data_file)

    artist_uris_done = []
    if os.path.isfile('emb/artist.emb.u'):
        artist_uris_done = np.array([line.strip() for line in open('emb/artist.emb.u', 'r')])

    for f in feature_list:
        if 'embedding' in f:
            emb_f = f['embedding']
            if feat_len.get(emb_f, None) is None:
                feat_len[emb_f] = count_emb_len(emb_f)

    # giuseppeverdi = '<http://data.doremus.org/artist/b82c0771-5280-39af-ad2e-8ace2f4ebda3>'
    big_query = """select DISTINCT * where {
                  ?a a ecrm:E21_Person .
                  [] ecrm:P14_carried_out_by ?a .
                } ORDER BY DESC(COUNT(?a))"""

    sparql.setQuery(big_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    with open('emb/artist.emb.h', 'w') as fh:
        fh.write(' '.join([ft['label'].replace(' ', '_') for ft in feature_list]))
        fh.write('\n')
        fh.write(' '.join([str(feat_len[ft.get('embedding', 'default')]) for ft in feature_list]))

    for result in results["results"]["bindings"]:
        uri = result['a']['value']
        if uri in artist_uris_done:
            continue

        print(uri)
        artist = flatten([get_partial_emb(f, "<%s>" % uri) for f in feature_list])

        with open('emb/artist.emb.v', 'a+') as f:
            nums = [str(n) for n in artist]
            f.write(' '.join(nums))
            f.write('\n')

        with open('emb/artist.emb.u', 'a+') as fu:
            fu.write(uri)
            fu.write('\n')


def flatten(lst=None):
    if lst is None:
        lst = []

    return [item for sublist in lst for item in sublist]


if __name__ == '__main__':
    main()
