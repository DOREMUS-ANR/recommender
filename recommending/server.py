from flask import Flask, jsonify
import recommend

app = Flask(__name__)


@app.route('/expression/<string:exp>')
def recommend_expression(exp):
    recommend.main({'expression': 'http://data.doremus.org/expression/%s' % exp})
    return jsonify({'done': True})

# export LC_ALL=en_US.UTF-8
# export LANG=en_US.UTF-8
# FLASK_APP=server.py flask run
