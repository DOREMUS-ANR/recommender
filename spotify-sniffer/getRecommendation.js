/*************************************
* Simulate recommendation from Spotify
* starting from the seed specified in
* config.json
*************************************/
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
      }).then((data) => {
        var track = data.body.tracks.items[0];

        let recOptions = {
          seed_tracks: [track.id]
        };

        return spotifyApi.getRecommendations(recOptions);
      })
      .then(readData)
      .then((res) => {
        res.input = seed;
        callback(null, res);
      }).catch(callback);
  }, function(err, results) {
    if (err) return console.error(err);

    fs.writeFileSync('output.json', JSON.stringify(results, null, 2));
    console.log('done');
  });

}

function getArtistIds(trackList) {
  let artist_list = trackList.map(track => track.artists);
  return flatten(artist_list).map(artist => artist.id);
}

function readData(data) {
  let trackList = data.body.tracks;

  return Promise.all([
    spotifyApi.getAudioFeaturesForTracks(trackList.map(track => track.id))
    .then((data) => data.body.audio_features),
    spotifyApi.getAlbums(trackList.map(track => track.album.id))
    .then((data) => data.body.albums),
    getArtistsInfo(getArtistIds(trackList))
  ]).then(values => {
    let [track_list, album_list, artist_list] = values;

    trackList.forEach((track, i) => {
      Object.assign(track, track_list[i]);
      track.album = album_list[i];
      track.artists.forEach((artist, j) => {
        track.artists[j] = artist_list.shift();
      });
    });

    return filterFeatures(trackList);
  });
}

function getArtistsInfo(artistIds, previousData = []) {
  return spotifyApi.getArtists(artistIds.splice(0, 50))
    .then((data) => {
      Array.prototype.push.apply(previousData, data.body.artists);

      if (!artistIds.length) return previousData;
      return getArtistsInfo(artistIds, previousData, callback);
    });
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

function flatten(arr) {
  return arr.reduce((a, b) => a.concat(Array.isArray(b) ? flatten(b) : b), []);
}
