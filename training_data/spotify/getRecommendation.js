/** ***********************************
* Simulate recommendation from Spotify
* starting from the seed specified in
* config.json
************************************ */
const fs = require('fs');
const async = require('async');
const spotifyAuth = require('./spotifyAuth');
const config = require('./config.json');

const {
  seeds,
} = config;

let spotifyApi;


function flatten(arr) {
  return arr.reduce((a, b) => a.concat(Array.isArray(b) ? flatten(b) : b), []);
}

function filterFeatures(array) {
  console.log(array[0]);

  return array.map((input) => {
    const output = {
      id: input.id,
      name: input.name,
      key: input.key,
      mode: input.mode,
      album_name: input.album.name,
      album_genre: input.album.genres,
    };
    for (const artist of input.artists) {
      output.artist_name = artist.name;
      output.artist_genre = artist.genres;
    }

    return output;
  });
}

function getArtistIds(trackList) {
  const artistList = trackList.map(track => track.artists);
  return flatten(artistList).map(artist => artist.id);
}
function getArtistsInfo(artistIds, previousData = []) {
  return spotifyApi.getArtists(artistIds.splice(0, 50))
    .then((data) => {
      Array.prototype.push.apply(previousData, data.body.artists);

      if (!artistIds.length) return previousData;
      return getArtistsInfo(artistIds, previousData);
    });
}


function readData(data_) {
  const { tracks } = data_.body;

  return Promise.all([
    spotifyApi.getAudioFeaturesForTracks(tracks.map(track => track.id))
      .then(data => data.body.audio_features),
    spotifyApi.getAlbums(tracks.map(track => track.album.id))
      .then(data => data.body.albums),
    getArtistsInfo(getArtistIds(tracks)),
  ]).then((values) => {
    const [trackList, albumList, artistList] = values;

    trackList.forEach((track, i) => {
      Object.assign(track, trackList[i]);
      track.album = albumList[i];
      track.artists.forEach((_artist, j) => {
        track.artists[j] = artistList.shift();
      });
    });

    return filterFeatures(trackList);
  });
}


function run(api) {
  spotifyApi = api;
  async.map(seeds, (seed, callback) => {
    spotifyApi.searchTracks(seed, {
      limit: 1,
    }).then((data) => {
      const track = data.body.tracks.items[0];

      const recOptions = {
        seed_tracks: [track.id],
      };

      return spotifyApi.getRecommendations(recOptions);
    })
      .then(readData)
      .then((res) => {
        res.input = seed;
        callback(null, res);
      })
      .catch(callback);
  }, (err, results) => {
    if (err) throw err;

    fs.writeFileSync('output.json', JSON.stringify(results, null, 2));
    console.log('done');
  });
}

spotifyAuth.login().then(run)
  .catch(e => console.error(e));
