Overture Music Recommender System
=================================

This folder contains the implementation of a music recommender system that will be host on [Overture](http://overture.doremus.org).

It works through embeddings computed through [__entity2vec__](https://github.com/MultimediaSemantics/entity2vec)

## Train

    python -m recommend --expression http://data.doremus.org/expression/7ce787df-e214-3d9b-a023-5439a7816d94

Parameters (the ones marked with **\*** are required):

| param                    | short  | default           | description |
|--------------------------|--------|-------------------|-------------|
| `--train` **\***         |        |                   | The train set. |
| `--test` **\***          |        |                   | The test set. |
| `--properties`           |        | ./properties.json | The properties file to pass to _entity2vec_ |

## Recommend

    python -m recommend --expression http://data.doremus.org/expression/7ce787df-e214-3d9b-a023-5439a7816d94

Parameters (the ones marked with **\*** are required):

| param                    | short  | default           | description |
|--------------------------|--------|-------------------|-------------|
| `--expression` **\***    | `-exp` |                   | The expression to be used as seed of the recommendation. |
| `--properties`           |        | ./properties.json | The properties file to pass to _entity2vec_ |
