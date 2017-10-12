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

### combine embeddings

It produce an embedding that combined different features.
It works for now for artists.

## get neighborhood

Returns a list of the most similar artist to the seed `-s`

    python get_neighborhood.py -cf artist -s http://data.doremus.org/artist/269cec9d-5025-3a8a-b2ef-4f7acb088f2b

## tell me why

Explains why 2 artists (seed `-s` and target `-t`) are similar

    python tell_me_why.py -cf artist -s http://data.doremus.org/artist/269cec9d-5025-3a8a-b2ef-4f7acb088f2b -t http://data.doremus.org/artist/438fe235-e00d-3864-befa-467398df6748


