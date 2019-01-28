#!/usr/bin/env python
import argparse
import json
import concurrent
from types import SimpleNamespace
from flask import Flask, jsonify, request
from flask_restplus import inputs
from werkzeug.exceptions import BadRequest
from recommender.recommender import Recommender
from recommender.explainator import Explainator
from recommender.utils import WeightsManager


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=argparse.FileType('r'), default='config/config.json',
                        help='Path of configuration file.')

    args, _ = parser.parse_known_args()
    return args


def load_config(file):
    cfg = json.load(file)
    if type(cfg) == dict:
        cfg = SimpleNamespace(**cfg)

    return cfg


app = Flask(__name__)

import os

if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
    print('init server...')
    args = parse_args()

    config = load_config(args.config)

    wm = WeightsManager(config)

    recs = {
        'artist': Recommender('artist', config.embDir, wm),
        'expression': Recommender('expression', config.embDir, wm)
    }


@app.route('/<string:entity_type>/<string:seed>')
def recommend(entity_type, seed):
    if entity_type not in recs:
        raise BadRequest('Type %s not recognised' % entity_type)

    recommender = recs[entity_type]

    uri = 'http://data.doremus.org/%s/%s' % (entity_type, seed)
    print('recommending %s %s' % (entity_type, uri))

    n = int(request.args.get('n', type=int, default=-1))  # how many recommendations?
    w = request.args.get('w', default=None)  # weights
    if w is not None:
        w = list(map(int, w.split(",")))

    explain = request.args.get('explain', type=inputs.boolean, default=False)

    most_similar = recommender.recommend(uri, n=n, w=w, target=request.args.get('target', default='default'),
                                         focus=request.args.get('focus', default=None))

    if explain:
        exp = Explainator(entity_type, seed, most_similar[0].seed, w, config)
        # we can swap out ProcessPoolExecutor for ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for result in executor.map(exp.explain, most_similar):
                pass
    return jsonify([x.toJson() for x in most_similar])

#
# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0')

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
# FLASK_APP=server.py flask run
