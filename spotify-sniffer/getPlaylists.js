const fs = require('fs'),
  async = require('async'),
  noop = require('noop'),
  Track = require('./Track'),
  matcher = require('../RF-WebRadio-Converter/matcher.js'),
  spotifyAuth = require('./spotifyAuth');

const config = require('./config.json');

// for taking them from play.spotify.com
// a = Array.prototype.map.call($0.querySelectorAll('.mo-info-name'), o => {
//   let part = o.href.split('/');
//   return {
//     user: part[4],
//     id: part[6]
//   };
// });
// JSON.stringify(a);


var {
  playlists,
  full
} = config;

var spotifyApi;
spotifyAuth.login(run);

function run(err, api) {
  if (err) return;
  spotifyApi = api;

  async.map(playlists, (playlist, callback) => {
    let outPath =`output/playlists/json/${playlist.id}.json`;
    if(!full && fs.existsSync(outPath)){
      return callback();
    }
    spotifyApi.getPlaylist(playlist.user, playlist.id)
      .then((data) => {
        data = data.body;
        playlist.name = data.name;
        playlist.followers = data.followers.total;

        let trackList = [];
        data.tracks.items.forEach((t) => {
          let track = new Track(t.track);
          trackList.push(track);
          // console.log(track.artists[0] + ' | ' + track.title);
        });
        playlist.tracks = trackList;
        async.eachSeries(trackList, (r, cb) => {
          let title = r.title.toLowerCase(),
            composer = r.artists[0].toLowerCase();
          matcher(composer, title, (err, bests) => {
            if (bests && bests[0]) {
              let best = bests[0];
              if (best.score >= 0.7) {
                r.best = best.expression;
                r.best_matching_score = best.score.toFixed(2);
              }
            }
            cb();
          });
        }, err => {
          if (err)
            console.error(err);
          else {
            let matched = playlist.tracks.filter(t=>t.best).length;
            playlist.n_matched = matched;
            playlist.n_total = playlist.tracks.length;
            console.log(`Playlist ${playlist.id} "${playlist.name}"
            matched: ${matched}`);
            fs.writeFileSync(outPath, JSON.stringify(playlist, null, 2));
          }
          callback(err, playlist);
        });

      }, callback);
  }, function(err, results) {
    if (err) return printError(err);

    console.log('done');
  });
}
