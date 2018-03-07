import json
import numpy as np
import os
import codecs
from types import SimpleNamespace
from SPARQLWrapper import SPARQLWrapper, JSON
from sklearn.decomposition import PCA

import config as cs
from .config import config

XSD_NAMESPACE = 'http://www.w3.org/2001/XMLSchema#'

sparql = SPARQLWrapper(config.endpoint)
feat_len = {
    'default': 1
}

embedding_cache = dict()


def load_embedding(file):
    if file in embedding_cache:
        return embedding_cache[file]

    emb_root = config.embDir

    vectors = np.loadtxt('%s/%s.emb.v' % (emb_root, file))
    uris = np.array([line.strip() for line in codecs.open('%s/%s.emb.u' % (emb_root, file), 'r', 'utf-8')])

    # dimensionality reduction
    pca = PCA(n_components=3)
    pca.fit(vectors)
    vectors = pca.transform(vectors)

    embedding_cache[file] = vectors, uris
    return vectors, uris


def get_embed(uri, emb):
    vectors, uris = load_embedding(emb)

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
    vectors, uris = load_embedding(emb)
    return len(vectors[0])


def main():
    what = config.chosenFeature

    with open('%s-similarity.json' % what) as json_data_file:
        _json = json.load(json_data_file)

    feature_list = sorted(_json['features'], key=lambda x: x['group'])
    main_query_select = _json['select']

    entity_uris_done = []

    uri_file = '%s/%s.emb.u' % (config.embDir, what)
    label_file = '%s/%s.emb.l' % (config.embDir, what)
    vector_file = '%s/%s.emb.v' % (config.embDir, what)
    header_file = '%s/%s.emb.h' % (config.embDir, what)

    if os.path.isfile(uri_file):
        entity_uris_done = np.array([line.strip() for line in open(uri_file, 'r')])

    for f in feature_list:
        if 'embedding' in f:
            emb_f = f['embedding']
            if feat_len.get(emb_f, None) is None:
                feat_len[emb_f] = f['dimensions'] or count_emb_len(emb_f)

    # giuseppeverdi = '<http://data.doremus.org/artist/b82c0771-5280-39af-ad2e-8ace2f4ebda3>'
    main_query = "SELECT DISTINCT ?a SAMPLE(?label) AS ?label " \
                 "WHERE { %s . OPTIONAL { ?a rdfs:label ?label } }" \
                 " GROUP BY ?a" \
                 " ORDER BY DESC(COUNT(?a))" % main_query_select
    print(main_query)

    sparql.setQuery(main_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    head = []
    last = None
    for ft in feature_list:
        label = ft['label']
        cur = {
            'label': label,
            'emb': 0
        }
        if last and last['label'] == label:
            cur = last
        else:
            head.append(cur)
        cur['emb'] += feat_len[ft.get('embedding', 'default')]
        last = cur

    with open(header_file, 'w') as fh:
        fh.write(' '.join([h['label'].replace(' ', '_') for h in head]))
        fh.write('\n')
        fh.write(' '.join([str(h['emb']) for h in head]))

    results = results["results"]["bindings"]
    for i, result in enumerate(results):
        uri = result['a']['value']
        if uri in entity_uris_done:
            continue

        label = result['label']['value'] if ('label' in result) else 'no_label'

        print('%d/%d %s' % (i, len(results), uri))
        vector = flatten([get_partial_emb(f, "<%s>" % uri) for f in feature_list])

        with open(label_file, 'a+') as lf:
            lf.write(label)
            lf.write('\n')

        with open(vector_file, 'a+') as f:
            nums = [str(n) for n in vector]
            f.write(' '.join(nums))
            f.write('\n')

        with open(uri_file, 'a+') as fu:
            fu.write(uri)
            fu.write('\n')


def flatten(lst=None):
    if lst is None:
        lst = []

    return [item for sublist in lst for item in sublist]


if __name__ == '__main__':
    cs.parse_args()
    main()
