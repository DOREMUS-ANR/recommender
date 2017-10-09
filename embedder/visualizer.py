import numpy as Math
import pylab as Plot
import codecs

from lib.tsne import tsne
import config as cs
from config import config


def main():
    glove_matrix = Math.loadtxt('emb/%s.emb.v' % config.chosenFeature)
    glove_words = [line.strip() for line in codecs.open('emb/%s.emb.l' % config.chosenFeature, 'r', 'utf-8')]

    target_words = glove_words

    rows = [glove_words.index(word) for word in target_words if word in glove_words]
    target_matrix = glove_matrix[rows, :]
    reduced_matrix = tsne(target_matrix, 2)

    Plot.figure(figsize=(200, 200), dpi=100)
    max_x = Math.amax(reduced_matrix, axis=0)[0]
    max_y = Math.amax(reduced_matrix, axis=0)[1]
    Plot.xlim((-max_x, max_x))
    Plot.ylim((-max_y, max_y))

    Plot.scatter(reduced_matrix[:, 0], reduced_matrix[:, 1], 20)

    for row_id in range(0, len(rows)):
        target_word = glove_words[rows[row_id]]
        x = reduced_matrix[row_id, 0]
        y = reduced_matrix[row_id, 1]
        Plot.annotate(target_word, (x, y))

    Plot.savefig("%s.png" % config.chosenFeature)


if __name__ == '__main__':
    cs.parse_args()
    main()
