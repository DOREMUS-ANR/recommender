Scripts for making the embeddings.

They all read the file `config_prod.json`, in particular the field `chosenFeature`.

### `create_edgelists.py`

It performs queries to the SPARQL endpoint, creating an edgelist for each query in the `sparqlDir` folder.

### `embed.py`

It realises the embedding through node2vec, in the implementation of [entity2vec](https://github.com/MultimediaSemantics/entity2vec/blob/master/entity2vec/node2vec.py).

### `post_embed.py`

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

    python get_neighborhood.py -cf artist -s http://data.doremus.org/artist/269cec9d-5025-3a8a-b2ef-4f7acb088f2b # bach
    python get_neighborhood.py -cf artist -s http://data.doremus.org/artist/b34f92ab-ad86-361b-a8b8-5c3a4db784d0 # vivaldi
    python get_neighborhood.py -cf expression -s http://data.doremus.org/expression/a9dd5b7e-4541-3654-9a45-af2ab36c320c # La Traviata

## tell me why

Explains why 2 artists (seed `-s` and target `-t`) are similar

    python tell_me_why.py -cf artist -s http://data.doremus.org/artist/269cec9d-5025-3a8a-b2ef-4f7acb088f2b -t http://data.doremus.org/artist/88458f1f-b751-3dbd-b081-b2cf5f20f225 # bach and caldara
    python tell_me_why.py -cf artist -s http://data.doremus.org/artist/b34f92ab-ad86-361b-a8b8-5c3a4db784d0 -t http://data.doremus.org/artist/a82b0c56-ccdf-31b6-a8b4-ad065f3405e5 # vivaldi and albinoni

python tell_me_why.py -cf artist -s http://data.doremus.org/artist/5425efed-002f-3638-a7b0-ad379a2bf63d -t http://data.doremus.org/artist/0d3493ff-b0f9-35c3-bc75-1adfc0150cd2


python recommender.py -cf artist -s  http://data.doremus.org/artist/f21bdcb3-565c-3a69-aa3f-67680a28e824


python tell_me_why.py -cf artist -s http://data.doremus.org/artist/b34f92ab-ad86-361b-a8b8-5c3a4db784d0 0.9999269773985313


