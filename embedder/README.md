Scripts for making the embeddings.

They all read the file `config.json`, in particular the field `chosenFeature`.

### `sparql2edgelist.py`

It performs queries to the SPARQL endpoint, creating an edgelist for each query in the `sparqlDir` folder.

### `embed.py`

It realises the embedding through node2vec, in the implementation of [entity2vec](https://github.com/MultimediaSemantics/entity2vec/blob/master/entity2vec/node2vec.py).

### `post-embed.py`

- It filters the embeddings following the `namespaces` defined in the config file.
- It produces 3 files:
  - Labels `*.emb.l`
  - URIs `*.emb.u`
  - Vectors `*.emb.v`

### `visualizer.py`

It produce a 2-dimensional map of the chosen feature embedding, using [tsne](https://github.com/MarcCote/learn2track/blob/master/learn2track/tsne.py)
