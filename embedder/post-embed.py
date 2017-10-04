from SPARQLWrapper import SPARQLWrapper, JSON

import codecs
import numpy as np
from config import config


def getLabel(uri):
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
    embeddings_file = 'emb/mop.emb'
    words = []
    vectors = []
    full = []

    namespaces = ["http://data.doremus.org/vocabulary/iaml/mop/",
                  "http://data.doremus.org/vocabulary/redomi/mop/",
                  "http://data.doremus.org/vocabulary/itema3/mop/",
                  "http://data.doremus.org/vocabulary/diabolo/mop/",
                  "http://www.mimo-db.eu/InstrumentsKeywords"]

    header = None
    with open(embeddings_file, 'r') as f:
        for line in f:
            if header is None:
                header = line
                continue

            fields = line.split()
            word = fields[0]
            vector = np.fromiter((float(x) for x in fields[1:]),
                                 dtype=np.float)

            if not any(ext in word for ext in namespaces):
                continue

            words.append(word)
            vectors.append(vector)
            full.append([getLabel(word), vector.flatten()])

    with open(embeddings_file + '.v', 'w') as f:
        with codecs.open(embeddings_file + '.l', 'w', "utf-8") as fl:
            for a in full:
                nums = [str(n) for n in a[1]]
                fl.write(a[0] + '\n')
                f.write(' '.join(nums))
                f.write('\n')


if __name__ == '__main__':
    main()
