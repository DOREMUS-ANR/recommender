import sys
from flask import Flask, jsonify, request
# import concurrent.futures
# from itertools import repeat

# from embedder import tell_me_why
from recommender.recommender import Recommender
import embedder.config as cs

config = cs.getConfig()

sys.path.pop(0)

app = Flask(__name__)

emb_dir = config.embDir
artistRec = Recommender('artist', emb_dir)
worksRec = Recommender('expression', emb_dir)


@app.route('/expression/<string:exp>')
def recommend_expression(exp):
    return jsonify(recommend("expression", exp, worksRec, request))


@app.route('/artist/<string:artist>')
def recommend_artist(artist):
    return jsonify(recommend("artist", artist, artistRec, request))


def recommend(entity_type, seed, recommender, rq):
    uri = 'http://data.doremus.org/%s/%s' % (entity_type, seed)
    print('recommending %s %s' % (entity_type, uri))

    n = int(rq.args.get('n', default=-1))  # how many recommendations?
    w = rq.args.get('w', default=None)  # weights
    if w is not None:
        w = list(map(int, w.split(",")))

    # explain = rq.args.get('explain', default=True)
    # if explain == "false":
    #     explain = False
    # print('n=%d' % n)

    most_similar = recommender.recommend(uri, n=n, w=w, target=rq.args.get('target', default=''),
                                         focus=rq.args.get('focus', default=None))

    # if explain:
    #     # we can swap out ProcessPoolExecutor for ThreadPoolExecutor
    #     with concurrent.futures.ThreadPoolExecutor() as executor:
    #         for result in executor.map(twCall, repeat(uri), repeat(entity_type), most_similar):
    #             pass

    return most_similar


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
