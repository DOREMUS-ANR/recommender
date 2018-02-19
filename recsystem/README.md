Overture Music Recommender System
=================================

This folder contains the implementation of a music recommender system that will be host on [Overture](http://overture.doremus.org).

It works through embeddings computed through [__entity2vec__](https://github.com/MultimediaSemantics/entity2vec).

It is exposed through on a Flask server.

## Flask server

    python server.py

## Docker

Build

    docker build -t doremus/recommender .

Run

    docker run -d --restart=unless-stopped  -v /var/docker/doremus/recommender/recsystem/recommending/data:/data -v /var/docker/doremus/recommender/recsystem/recommending/emb:/emb -v /var/docker/doremus/recommender/recsystem/config:/config -v /var/docker/doremus/recommender/recsystem/embedder/emb:/emb2 -v /var/docker/doremus/recommender/recsystem/recommending/features:/features -t --network doremus --name recommender doremus/recommender


<!-- docker run -d --restart=unless-stopped -v  /Users/pasquale/git/recommender/recsystem/config:/config -v /Users/pasquale/git/recommender/embeddings:/emb --network doremus -t --name recommender doremus/recommender -->


Stop

    docker stop recommender
    docker rm recommender ##remove from available containers
    docker rmi doremus/recommender ##remove from images
