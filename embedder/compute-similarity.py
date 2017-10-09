import json
import numpy as np
import pylab as Plot
import codecs
from types import SimpleNamespace
from SPARQLWrapper import SPARQLWrapper, JSON

from config import config

XSD_NAMESPACE = 'http://www.w3.org/2001/XMLSchema#'


def get_embed(uri, emb):
    vectors = np.loadtxt('emb/%s.emb.v' % emb)
    # labels = [line.strip() for line in codecs.open('emb/%s.emb.l' % config.chosenFeature, 'r', 'utf-8')]
    uris = np.array([line.strip() for line in codecs.open('emb/%s.emb.u' % emb, 'r', 'utf-8')])

    index = np.where(uris == uri)
    return vectors[index][0]


def to_embed(obj, emb):
    global XSD_NAMESPACE

    type = obj['type']
    value = obj['value']

    if type == 'uri':
        return get_embed(value, emb)

    if type == 'literal':
        v = value.replace(" ", '_')
        return 0

    if type == 'typed-literal' and obj['datatype'].startswith(XSD_NAMESPACE):
        # is a date!
        return int(value[:4]) / 2100

    return 0


def main():
    giuseppeverdi = '<http://data.doremus.org/artist/b82c0771-5280-39af-ad2e-8ace2f4ebda3>'
    sparql = SPARQLWrapper(config.endpoint)

    with open('artist-similarity.json') as json_data_file:
        feature_list = json.load(json_data_file)

    for f in feature_list:
        f = SimpleNamespace(**f)
        print(f.label)

        # setup query
        query = "SELECT * where { %s }" % f.query.replace('?a', giuseppeverdi)

        # perform query
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        emb = getattr(f, 'embedding', None)

        all_embs = [to_embed(result['o'], emb) for result in results["results"]["bindings"]]
        m = np.mean(all_embs, axis=0)
        print(m)

if __name__ == '__main__':
    main()
