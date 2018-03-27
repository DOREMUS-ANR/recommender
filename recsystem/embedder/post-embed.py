import codecs
import numpy as np
import sklearn.preprocessing as skpreprocess
from SPARQLWrapper import SPARQLWrapper, JSON

import config as cs
from config import config


def get_label(uri):
    print(uri)
    query = "select sql:BEST_LANGMATCH(?o, 'en;q=0.9, en-gb;q=0.8, *;q=0.1', 'en') as ?label" \
            " where { <%s> skos:prefLabel ?o }" % uri

    sparql = SPARQLWrapper(config.endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    r = results["results"]["bindings"][0]
    if r is None or 'label' not in r:
        return None
    return r["label"]["value"]


def main():
    what = config.chosenFeature
    embeddings_file = '%s/%s.emb' % (config.embDir, what)
    vectors = []
    labels = []
    uris = []

    chosen = config.features[config.chosenFeature]

    header = None
    with codecs.open(embeddings_file, 'r', 'utf-8') as f:
        for line in f:
            if header is None:
                header = line
                continue

            fields = line.split()
            word = fields[0]
            vector = np.fromiter((float(x) for x in fields[1:]),
                                 dtype=np.float)

            if 'namespaces' in chosen:
                namespaces = chosen['namespaces']
                if not any(ext in word for ext in namespaces):
                    continue

            lb = get_label(word)
            if lb is None:
                continue

            vectors.append(vector.flatten())
            labels.append(lb)
            uris.append(word)

    # vectors = skpreprocess.normalize(np.power(np.array(vectors, dtype=np.float), 3), 'l2', 0)
    vectors = skpreprocess.normalize(np.array(vectors, dtype=np.float), 'l2', 0)
    # why? because of https://www.quora.com/Should-I-do-normalization-to-word-embeddings-from-word2vec-if-I-want-to-do-semantic-tasks

    with open(embeddings_file + '.v', 'w') as f:
        for a in vectors:
            nums = [str(n) for n in a]
            f.write(' '.join(nums))
            f.write('\n')

    with open(embeddings_file + '.u', 'w') as fu:
        fu.write('\n'.join(uris))

    with codecs.open(embeddings_file + '.l', 'w', 'utf-8') as fl:
        fl.write('\n'.join(labels))


if __name__ == '__main__':
    cs.parse_args()
    main()
