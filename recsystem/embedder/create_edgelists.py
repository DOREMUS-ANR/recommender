import os
from os import path
import argparse
from types import SimpleNamespace

from SPARQLWrapper import SPARQLWrapper, JSON
import networkx as nx

XSD_NAMESPACE = 'http://www.w3.org/2001/XMLSchema#'


def main(args):
    all_query_files = [qf for qf in os.listdir(args.sparqlDir) if qf.endswith(".rq")]

    files = [args.feature] if args.feature else all_query_files

    for query_file in files:
        query2edgelist(query_file, args)


def query2edgelist(query_file, args):
    sparql = SPARQLWrapper(args.endpoint)

    with open(path.join(args.sparqlDir, query_file), 'r') as qf:
        query = qf.read()

        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        G = nx.Graph()
        for result in results["results"]["bindings"]:
            G.add_edge(to_node(result['s']), to_node(result['o']))

        out_file = path.join(args.edgelistDir, query_file.replace(".rq", ".edgelist"))
        nx.write_edgelist(G, out_file, data=False)


def to_node(obj):
    global XSD_NAMESPACE

    type = obj['type']
    value = obj['value']

    if type == 'uri':
        return value

    if type == 'literal':
        return value.replace(" ", '_')

    if type == 'typed-literal' and obj['datatype'].startswith(XSD_NAMESPACE):
        try:
            # is a date! to half century
            decade = 5 if (int(value[3]) > 4) else 0
            return value[:2] + str(decade) + '0'
        except:
            return '_'

    return value
