import os
import codecs
from shutil import copyfile
from gensim.models import KeyedVectors
from SPARQLWrapper import SPARQLWrapper, JSON


def ns_filter(embeddings_file, namespaces):
    with open(embeddings_file) as file:
        raw_embs = [l.strip() for l in file]

    def belong_to_category(x):
        for prefix in namespaces:
            if x.startswith(prefix):
                return True
        return False

    n = list(filter(belong_to_category, raw_embs))

    head = '%d %s' % (len(n), raw_embs[0].split(' ')[1])

    embeddings_temp = embeddings_file + "_temp"
    with open(embeddings_temp, 'w') as f:
        f.write("%s" % head)
        for item in n:
            f.write("\n%s" % item)
    return embeddings_temp


def get_label(uri, endpoint):
    query = "select sql:BEST_LANGMATCH(?o, 'en;q=0.9, en-gb;q=0.8, *;q=0.1', 'en') as ?label" \
            " where { <%s> skos:prefLabel ?o }" % uri

    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    r = results["results"]["bindings"][0]
    if r is None or 'label' not in r:
        print(uri)
        return None
    return r["label"]["value"]


def main(args):
    what = args.feature
    if what is None:
        raise RuntimeError('You must specify the feature using -f or --feature')

    chosen = args.featureList[what]
    namespaces = chosen['namespaces'] if 'namespaces' in chosen else False

    embeddings_file = '%s/%s.emb' % (args.embDir, what)
    embeddings_run = embeddings_file
    copyfile(embeddings_file, embeddings_file + '_raw')

    if namespaces:
        embeddings_run = ns_filter(embeddings_file, namespaces)

    # L2 normalisation
    # https://www.quora.com/Should-I-do-normalization-to-word-embeddings-from-word2vec-if-I-want-to-do-semantic-tasks
    wv_from_text = KeyedVectors.load_word2vec_format(embeddings_run)
    wv_from_text.init_sims(replace=True)
    labels = ['%s %s' % (uri, get_label(uri, args.endpoint)) for uri in wv_from_text.index2entity]

    with codecs.open(embeddings_file + '.l', 'w', 'utf-8') as fl:
        fl.write('\n'.join(labels))

    wv_from_text.save_word2vec_format(embeddings_file)
    if embeddings_run.endswith('_temp'):
        os.remove(embeddings_run)
