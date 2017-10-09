import codecs
import numpy as np
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
    return r["label"]["value"]


def main():
    what = config.chosenFeature
    embeddings_file = 'emb/%s.emb' % what
    vectors = []

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

            vectors.append([word, get_label(word), vector.flatten()])

    with open(embeddings_file + '.v', 'w') as f:
        with open(embeddings_file + '.u', 'w') as fu:
            with codecs.open(embeddings_file + '.l', 'w', 'utf-8') as fl:
                for a in vectors:
                    fu.write(a[0] + '\n')
                    fl.write(a[1] + '\n')

                    nums = [str(n) for n in a[2]]
                    f.write(' '.join(nums))
                    f.write('\n')


if __name__ == '__main__':
    cs.parse_args()
    main()
