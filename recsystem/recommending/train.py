#!/usr/bin/python

import argparse
import asyncio
import codecs
import json
import sys

from recommender.entity2entity import Entity2Rec


def main(args):
    print('Start training')
    properties_path = args.properties if args.properties else './properties.json'
    train_name = args.train[args.train.rfind('/') + 1:-4]
    test_name = args.test[args.test.rfind('/') + 1:-4]

    with codecs.open(properties_path, 'r', encoding='utf-8') as config_read:
        property_file = json.loads(config_read.read())

    properties = [i for i in property_file['doremus']]
    properties.append('combined')

    # TODO parametrize folders
    rec = Entity2Rec(False, False, False, 1, 1, 10, 5,
                     500, 10, 8, 5, properties_path, False, 'doremus', 'all', False,
                     args.train, args.test, False, False, args.feedback_file)
    # todo version with run all
    rec.run(False)

    emb_file_train = 'features/doremus/p1_q1/%s_p1_q1.svm' % train_name
    emb_file_test = 'features/doremus/p1_q1/%s_p1_q1.svm' % test_name

    loop = asyncio.get_event_loop()
    loop.run_until_complete(compute_ranklib(p, emb_file_train, emb_file_test))


async def compute_ranklib(cur_prop, emb_file_train, emb_file_test):
    cp = cur_prop.split(':')[-1]
    ranklib_cmd = 'java -jar bin/RankLib.jar' \
                  ' -save models/model_%s.txt -train %s -test %s' \
                  ' -ranker 6 -metric2t P@10 -tvs 0.9' \
                  % (cp, emb_file_train, emb_file_test)

    print("Start: %s" % ranklib_cmd)
    proc = await asyncio.create_subprocess_shell(
        ranklib_cmd, stdin=None, stderr=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    out = await proc.stdout.read()
    print(out)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", help="The train set.")
    parser.add_argument("--test", help="The test set.")
    parser.add_argument("--feedback_file", help="Path to a DAT file that contains all the couples of works.")
    parser.add_argument("--properties", nargs='?', default='./properties.json',
                        help="The properties file to pass to entity2vec.")

    args = parser.parse_args()

    if not hasattr(args, 'train'):
        print('The `train` option is required')
        sys.exit(1)

    if not hasattr(args, 'test'):
        print('The `test` option is required')
        sys.exit(1)

    main(args)
