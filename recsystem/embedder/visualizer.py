import numpy as np
import codecs
import os
from gensim.models import KeyedVectors

import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

OUT_PATH = './img'


def main(args):
    what = args.feature
    if what is None:
        raise RuntimeError('You must specify the feature using -f or --feature')

    labels_file = codecs.open('%s/%s.emb.l' % (args.embDir, what), 'r', 'utf-8')
    embedding = KeyedVectors.load_word2vec_format('%s/%s.emb' % (args.embDir, what))

    uris = embedding.index2entity
    vectors = [embedding.get_vector(k) for k in uris]
    labels = []
    for line in labels_file:
        key, value = line.strip().split(' ', 1)
        labels.append(value)

    # find tsne coords for 2 dimensions
    tsne = TSNE(n_components=2, random_state=0)
    np.set_printoptions(suppress=True)
    Y = tsne.fit_transform(vectors)

    x_coords = Y[:, 0]
    y_coords = Y[:, 1]

    # display scatter plot
    plt.scatter(x_coords, y_coords, alpha=0)

    if not args.show:
        plt.rcParams.update({'font.size': 0.5})

    for label, x, y in zip(labels, x_coords, y_coords):
        plt.annotate(label, xy=(x, y), xytext=(0, 0), textcoords='offset points')
    plt.xlim(x_coords.min() + 0.00005, x_coords.max() + 0.00005)
    plt.ylim(y_coords.min() + 0.00005, y_coords.max() + 0.00005)

    if args.show:
        plt.show()
    else:
        if not os.path.exists(OUT_PATH):
            os.makedirs(OUT_PATH)

        out = '%s/%s.eps' % (OUT_PATH, what)
        plt.savefig(out, format='eps', dpi=1200)
        print('Picture saved at %s' % out)
