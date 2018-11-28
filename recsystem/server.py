#!/usr/bin/env python
import argparse
import json
from types import SimpleNamespace
from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest
from recommender.recommender import Recommender
from recommender.weights import WeightsManager


# from embedder import tell_me_why

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=argparse.FileType('r'), default='config/config.json',
                        help='Path of configuration file.')

    return parser.parse_args()


def load_config(file):
    cfg = json.load(file)
    if type(cfg) == dict:
        cfg = SimpleNamespace(**cfg)

    return cfg


print('init server...')
app = Flask(__name__)

args = parse_args()
config = load_config(args.config)

wm = WeightsManager(config)

recs = {
    'artist': Recommender('artist', config.embDir, wm)
}


@app.route('/<string:entity_type>/<string:seed>')
def recommend(entity_type, seed):
    print(entity_type)
    if entity_type not in recs:
        raise BadRequest('Type %s not recognised' % entity_type)

    recommender = recs[entity_type]

    uri = 'http://data.doremus.org/%s/%s' % (entity_type, seed)
    print('recommending %s %s' % (entity_type, uri))

    n = int(request.args.get('n', default=-1))  # how many recommendations?
    w = request.args.get('w', default=None)  # weights
    if w is not None:
        w = list(map(int, w.split(",")))

    # explain = rq.args.get('explain', default=True)
    # if explain == "false":
    #     explain = False
    # print('n=%d' % n)

    most_similar = recommender.recommend(uri, n=n, w=w, target=request.args.get('target', default=''),
                                         focus=request.args.get('focus', default=None))

    # if explain:
    #     # we can swap out ProcessPoolExecutor for ThreadPoolExecutor
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         for result in executor.map(twCall, repeat(uri), repeat(entity_type), most_similar):
    #             pass
    return jsonify(most_similar)


# call to tell_me_why
# def twCall(uri, type, _a):
#     shared = tell_me_why.main(uri, _a['uri'], type)
#     _a['why'] = []
#     for s in shared:
#         selected = s['selected']
#
#         _a['why'].append({
#             'feature': s['label'],
#             'score': selected[0]['score'],
#             'values': [_x['o'] for _x in selected]
#         })
#
#     return 1


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
# FLASK_APP=server.py flask run
