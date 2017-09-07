#!/usr/bin/python

import argparse
import re
import subprocess
import sys
from types import SimpleNamespace
import os
from concurrent.futures import ThreadPoolExecutor as Pool

import numpy as np

from recommender.entity2entity import Entity2Rec

ranklib_res = False
emb_file_path = False

num_to_save = 20

curDir = '/'.join(str(__file__).split('/')[:-1])
if curDir == '':
    curDir = '/'
os.chdir(curDir)


# todo create training mode

class ScoredExpression:
    def __init__(self, uri, scoring):
        self.uri = uri
        self.scoring = scoring

    def __str__(self):
        return self.uri + '\t' + str(self.scoring)


def writeFile(file, content):
    file.write(content)
    file.flush()
    os.fsync(f.fileno())


def create_connection_file(exp):
    epx_id = exp[exp.rfind('/') + 1:]

    with open("all_expressions.txt") as all_exp_file:
        all_exp = all_exp_file.read()
        # remove last empty line
        if not all_exp[-1]:
            all_exp = all_exp[:-1]

    with open("data/all_connections/%s.edgelist" % epx_id, "w") as output:
        out = re.sub(r"^", exp + " ", all_exp, 0, re.MULTILINE)
        out = re.sub(r"$", " 0 0", out, 0, re.MULTILINE)
        output.write(out)


def parse_features(line):
    # 0 qid:1 1:0.500000 2:0.490216 3:0.640701 4:0.444151 # http://data.doremus.org/expression/1a31be0c-5a5b-3a42-8e6b-12988463d6be
    line = line[2:]
    parts = line.split('#')[0].strip().split(' ')[1:]
    features = [float(p.split(':')[1]) for p in parts]
    return np.array(features)


def emb2score(e):
    return np.mean(e)


def main(args):
    if type(args) == dict:
        args = SimpleNamespace(**args)

    exp = args.expression
    properties = args.properties if hasattr(args, 'properties') else './properties.json'
    seed_id = exp[exp.rfind('/') + 1:]

    print("create connection file")
    create_connection_file(exp)

    # TODO parametrize folders
    print("run e2rec")
    rec = Entity2Rec(False, False, False, 1, 1, 10, 5,
                     500, 10, 8, 5, properties, False,
                     'doremus', 'all', False,
                     'data/all_connections/%s.edgelist' % seed_id,
                     'data/e2e/test.dat',
                     False, False,
                     'data/e2e/feedback.edgelist')
    # todo version with run all
    rec.run(False)

    global ranklib_res
    global emb_file_path
    emb_file_path = 'features/doremus/p1_q1/%s_p1_q1.svm' % seed_id
    ranklib_res = 'data/ranklib_results/%s.txt' % seed_id

    #  todo generalize
    print("run ranklib")
    ranklib_cmd = 'java -jar bin/RankLib.jar' \
                  ' -load data/models/model_combined.txt -rank %s -score %s' \
                  % (emb_file_path, ranklib_res)

    pool = Pool(max_workers=1)
    f = pool.submit(subprocess.call, ranklib_cmd, shell=True)
    f.add_done_callback(lambda x: process_recommendation(seed_id))


def process_recommendation(seed_id):
    with open("all_expressions.txt") as all_exp_file:
        all_exp = all_exp_file.read().split("\n")
        if not all_exp[-1]:
            all_exp = all_exp[:-1]

    with open(ranklib_res) as score_file:
        score = score_file.read().strip().split("\n")
        if not score[-1]:
            score = score[:-1]

    with open(emb_file_path) as emb_file:
        emb = [parse_features(line) for line in emb_file.read().strip().split("\n")]

    # feature by feature
    for i in range(0, len(emb[0])):
        feat_scoring = []
        for exp in enumerate(all_exp):
            j = exp[0]
            uri = exp[1]
            if uri != 'http://data.doremus.org/expression/' + seed_id:
                feat_scoring.append(ScoredExpression(uri, emb[j][i]))
        feat_scoring.sort(key=lambda s: s.scoring, reverse=True)

        with open('data/scoring/%s_%d.tsv' % (seed_id, i), 'w') as output:
            writeFile(output, '\n'.join([str(e) for e in feat_scoring[0:20]]))

    # combined
    emb_score = [emb2score(e) for e in emb]
    score[:] = [float(re.sub(r'^\d+\t\d+\t', '', s).strip()) for s in score]

    score_exp = []
    for exp in enumerate(all_exp):
        i = exp[0]
        score_exp.append(ScoredExpression(exp[1], score[i] + 2 * emb_score[i]))

    score_exp.sort(key=lambda s: s.scoring, reverse=True)
    print("\n".join([str(s) for s in score_exp[0:15]]))
    with open('data/scoring/%s_combined.tsv' % seed_id, 'w') as output:
        writeFile(output, ('\n'.join([str(s) for s in score_exp[0:20]])))


def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-exp", "--expression", help="The expression to be used as seed of the recommendation")
    parser.add_argument("--properties", nargs='?', default='./properties.json', help="Run in training mode.")

    args = parser.parse_args()

    if not hasattr(args, 'expression'):
        print('The `expression` option is required')
        sys.exit(1)

    main(args)
