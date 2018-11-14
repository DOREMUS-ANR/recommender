

import common.config as cs

config = cs.getConfig()
config.chosenFeature = 'genre'


chosen = config.features[config.chosenFeature]
namespaces = chosen['namespaces'] if 'namespaces' in chosen else False



embeddings_file = '/Users/pasquale/git/music-embeddings/%s.emb' % config.chosenFeature



with open(embeddings_file) as file:
    raw_embs = [l.strip() for l in file]



def belongToCategory(x):
    for prefix in namespaces:
        if x.startswith(prefix):
            return True
    return False




n = list(filter(belongToCategory, raw_embs))




head = '%d %s' % (len(n),raw_embs[0].split(' ')[1])




embeddings_temp = './%s_temp.emb' % config.chosenFeature
with open(embeddings_temp, 'w') as f:
    f.write("%s" % head)
    for item in n:
        f.write("\n%s" % item)
with open(embeddings_temp) as file:
    a= [l.strip() for l in file]




from gensim.models import KeyedVectors



wv_from_text = KeyedVectors.load_word2vec_format(embeddings_temp, binary=False)



wv_from_text.index2entity[0:100]




wv_from_text.get_vector('http://data.doremus.org/vocabulary/iaml/genre/ct')



wv_from_text.most_similar('http://data.doremus.org/vocabulary/iaml/genre/ct')



wv_from_text.init_sims(replace=True)



wv_from_text.get_vector('http://data.doremus.org/vocabulary/iaml/genre/ct')



wv_from_text.most_similar('http://data.doremus.org/vocabulary/iaml/genre/ct')



wv_from_text.similar_by_word('http://data.doremus.org/vocabulary/iaml/genre/ct')

