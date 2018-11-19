import json
import numpy as np
import os
from types import SimpleNamespace
from SPARQLWrapper import SPARQLWrapper, JSON
from sklearn.decomposition import PCA
import sklearn.preprocessing as skpreprocess
from gensim.models import KeyedVectors

SIMILARITY_FOLDER = './similarity'
XSD_NAMESPACE = 'http://www.w3.org/2001/XMLSchema#'

feat_len = {
    'default': 1
}
feat_len_short = {
    'default': 1
}

embedding_cache = dict()


class CombineEmbeddings:
    def __init__(self, args):
        self.what = args.feature
        if self.what is None:
            raise RuntimeError('You must specify the feature using -f or --feature')

        self.emb_dir = args.embDir
        self.sparql = SPARQLWrapper(args.endpoint)
        self.reset = args.reset

    def load_embedding(self, file):
        if file in embedding_cache:
            return embedding_cache[file]

        embedding = KeyedVectors.load_word2vec_format('%s/%s.emb' % (self.emb_dir, file))

        uris = embedding.index2entity
        vectors = [embedding.get_vector(k) for k in uris]

        # dimensionality reduction
        pca = PCA(n_components=5)
        pca.fit(vectors)
        vectors_short = pca.transform(vectors)
        vectors_short = skpreprocess.normalize(np.array(vectors_short, dtype=np.float), 'l2', 0)

        embedding_cache[file] = vectors, vectors_short, uris
        return vectors, vectors_short, uris

    def get_embed(self, uri, emb, short=False):
        vectors, vectors_short, uris = self.load_embedding(emb)

        index = np.where(uris == uri)
        v = vectors_short if short else vectors
        return v[index][0] if len(index[0]) else None

    def to_embed(self, obj, emb, short=False):
        global XSD_NAMESPACE

        type = obj['type']
        value = obj['value']

        if type == 'uri':
            return self.get_embed(value, emb, short)

        if type == 'literal':
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

    def get_partial_emb(self, f, uri):
        f = SimpleNamespace(**f)
        # print(f.label)

        # setup query
        query = "SELECT * where { %s } " % f.query.replace('?a', uri)

        # perform query
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        bindings = results["results"]["bindings"]

        emb = getattr(f, 'embedding', None)

        all_embs = [self.to_embed(result['o'], emb) for result in bindings]
        all_embs = [x for x in all_embs if x is not None]

        all_embs_short = [self.to_embed(result['o'], emb, short=True) for result in bindings]
        all_embs_short = [x for x in all_embs_short if x is not None]

        if len(all_embs):
            feat_len[emb] = len(all_embs[0])
            return np.mean(all_embs, axis=0), np.mean(all_embs_short, axis=0)
        else:
            return np.ones(feat_len.get(emb, 1)) * -2, np.ones(feat_len_short.get(emb, 1)) * -2

    def count_emb_len(self, emb):
        vectors, vectors_short, uris = self.load_embedding(emb)
        return len(vectors[0])

    def run(self):
        with open('%s/%s.json' % (SIMILARITY_FOLDER, self.what)) as json_data_file:
            _json = json.load(json_data_file)

        feature_list = sorted(_json['features'], key=lambda x: x['group'])
        main_query_select = _json['select']

        uri_file = '%s/%s.emb.u' % (self.emb_dir, self.what)
        label_file = '%s/%s.emb.l' % (self.emb_dir, self.what)
        vector_file = '%s/%s.emb.long' % (self.emb_dir, self.what)
        vector_file_short = '%s/%s.emb' % (self.emb_dir, self.what)
        header_file = '%s/%s.emb.long.h' % (self.emb_dir, self.what)
        header_file_short = '%s/%s.emb.h' % (self.emb_dir, self.what)

        for f in feature_list:
            if 'embedding' in f:
                emb_f = f['embedding']
                if feat_len.get(emb_f, None) is None:
                    feat_len[emb_f] = self.count_emb_len(emb_f)
                feat_len_short[emb_f] = f['dimensions'] or 1

        main_query = "SELECT DISTINCT ?a SAMPLE(?label) AS ?label " \
                     "WHERE { %s . OPTIONAL { ?a rdfs:label ?label } }" \
                     " GROUP BY ?a" \
                     " LIMIT 10" % main_query_select
        # ORDER
        # BY
        # DESC(COUNT(?a))
        print(main_query)

        self.sparql.setQuery(main_query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()

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

        head_short = []
        for ft in feature_list:
            cur = {
                'label': ft['label'],
                'emb': ft['dimensions'] if 'dimensions' in ft else 1
            }
            head_short.append(cur)

        with open(header_file, 'w') as fh:
            fh.write(' '.join([h['label'].replace(' ', '_') for h in head]))
            fh.write('\n')
            fh.write(' '.join([str(h['emb']) for h in head]))

        with open(header_file_short, 'w') as fh:
            fh.write(' '.join([h['label'].replace(' ', '_') for h in head_short]))
            fh.write('\n')
            fh.write(' '.join([str(h['emb']) for h in head_short]))

        reset = self.reset or not os.path.isfile(uri_file)
        entity_uris_done = np.array([line.strip() for line in open(uri_file, 'r')]) if reset else []
        mode = 'w' if reset else 'a+'

        results = results["results"]["bindings"]
        for i, result in enumerate(results):
            uri = result['a']['value']
            if uri in entity_uris_done:
                continue

            label = result['label']['value'] if ('label' in result) else 'no_label'

            print('%d/%d %s' % (i, len(results), uri))
            vector = []
            vector_short = []
            for f in feature_list:
                long, short = self.get_partial_emb(f, "<%s>" % uri)
                vector.append(long)
                vector_short.append(short)

            vector = flatten(vector)
            vector_short = flatten(vector_short)

            with open(label_file, mode) as lf:
                lf.write(uri)
                lf.write(' ')
                lf.write(label.replace('\n', ' '))
                lf.write('\n')

            with open(vector_file, mode) as f:
                if mode == 'w':
                    f.write('%d %d' % (len(results), len(vector)))
                nums = [str(n) for n in vector]
                f.write(uri)
                f.write(' ')
                f.write(' '.join(nums))
                f.write('\n')

            with open(vector_file_short, mode) as f:
                if mode == 'w':
                    f.write('%d %d' % (len(results), len(vector_short)))
                nums = [str(n) for n in vector_short]
                f.write(uri)
                f.write(' ')
                f.write(' '.join(nums))
                f.write('\n')

            with open(uri_file, mode) as fu:
                fu.write(uri)
                fu.write('\n')


def flatten(lst=None):
    if lst is None:
        lst = []

    return [item for sublist in lst for item in sublist]
