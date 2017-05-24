const fs = require('fs'),
  async = require('async'),
  noop = require('noop'),
  spotifyAuth = require('./spotifyAuth');

const config = require('./config.json');


var {
  seeds
} = config;

var spotifyApi;
spotifyAuth.login(run);

function run(err, api) {
  if (err) return;
  spotifyApi = api;
  async.map(seeds, (seed, callback) => {

    spotifyApi.searchTracks(seed, {
        limit: 1
      })
      .then((data) => {
        var track = data.body.tracks.items[0];

        let recOptions = {
          seed_tracks: [track.id]
        };

        spotifyApi.getRecommendations(recOptions).then((data) => {
          readData(data, (err, res) => {
            if (err) return callback(err);
            res.input = seed;
            callback(null, res);
          });
        }, callback);

      }, callback);
  }, function(err, results) {
    if (err) return printError(err);

    fs.writeFileSync('output.json', JSON.stringify(results, null, 2));
    console.log('done');
  });

}


function readData(data, callbackFn) {
  let trackList = data.body.tracks;

  let track_list = [],
    album_list = [],
    artist_list = [];

  async.parallel([
    (callback) => {
      spotifyApi.getAudioFeaturesForTracks(trackList.map(track => track.id))
        .then(function(data) {
          track_list = data.body.audio_features;
          callback(null, album_list);
        }, callback);

    },
    (callback) => {
      spotifyApi.getAlbums(trackList.map(track => track.album.id))
        .then(function(data) {
          album_list = data.body.albums;
          callback(null, album_list);
        }, callback);
    },
    (callback) => {
      let artists = flatten(trackList.map(track => track.artists)).map(artist => artist.id);
      getArtistsInfo(artists, artist_list, callback);
    }
  ], function cb(err, data) {
    if (err) callbackFn(err);

    trackList.forEach((track, i) => {
      Object.assign(track, track_list[i]);
      track.album = album_list[i];

      track.artists.forEach((artist, j) => {
        track.artists[j] = artist_list.shift();
      });
    });

    callbackFn(null, filterFeatures(trackList));
  });


}

function getArtistsInfo(artistIds, previousData = [], callback = noop) {
  spotifyApi.getArtists(artistIds.splice(0, 50))
    .then((data) => {
      Array.prototype.push.apply(previousData, data.body.artists);

      if (!artistIds.length) callback(null, previousData);
      else getArtistsInfo(artistIds, previousData, callback);
    }, callback);
}

function filterFeatures(array) {
  console.log(array[0]);

  return array.map((input) => {
    var output = {
      id: input.id,
      name: input.name,
      key: input.key,
      mode: input.mode,
      album_name: input.album.name,
      album_genre: input.album.genres
    };
    for (let artist of input.artists) {
      output.artist_name = artist.name;
      output.artist_genre = artist.genres;
    }

    return output;
  });
}

function printError(err) {
  console.error(err);
}

function flatten(arr) {
  return arr.reduce((a, b) => a.concat(Array.isArray(b) ? flatten(b) : b), []);
}
