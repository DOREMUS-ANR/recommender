import sys
from flask import Flask, jsonify

from embedder import get_neighborhood, tell_me_why
from recommending import recommend

sys.path.pop(0)

app = Flask(__name__)


@app.route('/expression/<string:exp>')
def recommend_expression(exp):
    result = recommend.main({'expression': 'http://data.doremus.org/expression/%s' % exp})
    return jsonify(result)


@app.route('/artist/<string:artist>')
def recommend_artist(artist):
    uri = 'http://data.doremus.org/artist/%s' % artist
    print('recommending artist %s' % uri)
    most_similar = get_neighborhood.find(uri)
    for _a in most_similar:
        shared = tell_me_why.main(uri, _a['uri'])
        _a['why'] = []
        for s in shared:
            selected = s['selected']

            _a['why'].append({
                'feature': s['label'],
                'score': selected[0]['score'],
                'values': [_x['o'] for _x in selected]
            })

    return jsonify(most_similar)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
# FLASK_APP=server.py flask run
