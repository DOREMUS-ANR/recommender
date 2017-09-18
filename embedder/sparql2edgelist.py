#!/usr/bin/env python
import os
import json
from os import path
import argparse
from types import SimpleNamespace

from SPARQLWrapper import SPARQLWrapper, JSON
import networkx as nx

XSD_NAMESPACE = 'http://www.w3.org/2001/XMLSchema#'


def main(args):
    global sparql
    global config

    if type(args) == dict:
        args = SimpleNamespace(**args)

    init()

    all_query_files = [qf for qf in os.listdir(config.sparqlDir) if qf.endswith(".rq")]

    files = [args.file] if args.file else all_query_files

    for query_file in files:
        query2edgelist(query_file)


def init():
    global sparql
    global config

    with open('config.json') as json_data_file:
        config = json.load(json_data_file)

    if type(config) == dict:
        config = SimpleNamespace(**config)


    global sparql
    sparql = SPARQLWrapper(config.endpoint)

    if not os.path.exists(config.edgelistDir):
        os.makedirs(config.edgelistDir)


def query2edgelist(query_file):
    global sparql
    global config

    with open(path.join(config.sparqlDir, query_file), 'r') as qf:
        query = qf.read()

        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        G = nx.Graph()
        for result in results["results"]["bindings"]:
            G.add_edge(toNode(result['s']), toNode(result['o']))

        out_file = path.join(config.edgelistDir, query_file.replace(".rq", ".edgelist"))
        nx.write_edgelist(G, out_file, data=False)


def toNode(obj):
    global XSD_NAMESPACE

    type = obj['type']
    value = obj['value']

    if type == 'uri':
        return value

    if type == 'literal':
        return value.replace(" ", '_')

    if type == 'typed-literal' and obj['datatype'].startswith(XSD_NAMESPACE):
        # is a date! to half century
        decade = 5 if (int(value[3]) > 4) else 0
        return value[:2] + str(decade) + '0'

    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="The query file to address for the generation of edgelists")

    args = parser.parse_args()

    main(args)
