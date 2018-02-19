import sys
from flask import Flask, jsonify, request
import concurrent.futures
from itertools import repeat

from embedder import get_neighborhood, tell_me_why

# from recommending import recommend

sys.path.pop(0)

app = Flask(__name__)


@app.route('/expression/<string:exp>')
def recommend_expression(exp):
    # result = recommend.main({'expression': 'http://data.doremus.org/expression/%s' % exp})
    return jsonify(recommend_something("expression", exp, request))


@app.route('/artist/<string:artist>')
def recommend_artist(artist):
    return jsonify(recommend_something("artist", artist, request))


def recommend_something(type, seed, rq):
    uri = 'http://data.doremus.org/%s/%s' % (type, seed)
    print('recommending %s %s' % (type, uri))
    n = int(rq.args.get('n', default=-1))
    w = rq.args.get('w', default=None)
    if w is not None:
        w = list(map(int, w.split(",")))

    explain = rq.args.get('explain', default=True)
    if explain == "false":
        explain = False
    print('n=%d' % n)

    most_similar = get_neighborhood.find(uri, ftype=type, n=n, w=w)

    if explain:
        # we can swap out ProcessPoolExecutor for ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for result in executor.map(twCall, repeat(uri), repeat(type), most_similar):
                pass

    return most_similar


# call to tell_me_why
def twCall(uri, type, _a):
    shared = tell_me_why.main(uri, _a['uri'], type)
    _a['why'] = []
    for s in shared:
        selected = s['selected']

        _a['why'].append({
            'feature': s['label'],
            'score': selected[0]['score'],
            'values': [_x['o'] for _x in selected]
        })

    return 1


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
# FLASK_APP=server.py flask run
