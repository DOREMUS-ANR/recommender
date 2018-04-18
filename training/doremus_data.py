import numpy as np
import codecs
import os


def init(root_training, root_emb):
    global emb_dir, train_dir
    emb_dir = root_emb
    train_dir = root_training


def get_embeddings(what='expression'):
    uri_file = '%s/%s.emb.u' % (emb_dir, what)
    vector_file = '%s/%s.emb.v' % (emb_dir, what)
    header_file = '%s/%s.emb.h' % (emb_dir, what)
    label_file = '%s/%s.emb.l' % (emb_dir, what)

    # load embeddings
    vectors = np.array([line.strip().split(' ') for line in codecs.open(vector_file, 'r', 'utf-8')], np.float32)
    uris = np.array([line.strip() for line in codecs.open(uri_file, 'r', 'utf-8')])
    lbs = np.array([line.strip() for line in codecs.open(label_file, 'r', 'utf-8').read().split('\n')[:-1]])
    try:
        heads = np.array([line.strip() for line in codecs.open(header_file, 'r', 'utf-8')])

        # header for printing
        head_label = heads[0].split()
        head_val = heads[1].split()
        head_dim = []
        for i in range(0, len(head_val)):
            for j in range(0, int(head_val[i])):
                head_dim.append(head_label[i])

        heads_print = [head_label, head_val]
    except FileNotFoundError:
        head_dim = None
        heads_print = None

    return vectors, uris, lbs, head_dim, heads_print


def all_training(what='expression'):
    return [{
        'name': 'pp_concerts',
        'playlists': _load_training('concerts/output/list/philharmonie', what)
    }, {
        'name': 'itema3_concerts',
        'playlists': _load_training('concerts/output/list/itema3', what)
    }, {
        'name': 'web-radio',
        'playlists': _load_training('web-radio/output/list', what)
    }, {
        'name': 'spotify_pl',
        'playlists': _load_training('spotify/output/playlists/list', what)
    }]


def _load_training(sub, what='expression'):
    folder = os.path.join(train_dir, sub, what)
    playlists = []
    for f in sorted(os.listdir(folder)):
        file = '%s/%s' % (folder, f)
        data = np.array([line.strip() for line in codecs.open(file, 'r', 'utf-8')])
        playlists.append({
            'name': file,
            'data': data
        })

    return playlists
