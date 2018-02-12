/********************************
 * Retrieve the content of the
 * playlists in config.json
 * and interlink them with DOREMUS
 *********************************/

const fs = require('fs'),
  async = require('async'),
  noop = require('node-noop').noop,
  Track = require('./Track'),
  matcher = require('../matcher.js'),
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
  if (err) return console.error(err);
  spotifyApi = api;

  async.map(playlists, (playlist, callback) => {
    let outPath = `output/playlists/json/${playlist.id}.json`;
    if (!full && fs.existsSync(outPath))
      return callback();

    spotifyApi
      .getPlaylist(playlist.user, playlist.id)
      .then((data) => {
        data = data.body;
        playlist.name = data.name;
        playlist.followers = data.followers.total;

        playlist.tracks = data.tracks.items
          .map((t) => new Track(t.track));

        async.eachSeries(playlist.tracks, (r, cb) => {
          let title = r.title.toLowerCase(),
            composer = r.artists[0].toLowerCase();
          matcher(composer, title, (err, res) => {
            if (!res) return cb();
            if (res.composerUri) r.composer = res.composerUri;
            let bests = res.bests;
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
          if (err) console.error(err);
          else {
            let matched = playlist.tracks.filter(t => t.best).length;
            playlist.n_matched = matched;
            playlist.n_total = playlist.tracks.length;
            console.log(`Playlist ${playlist.id} "${playlist.name}"
            matched: ${matched}`);
            fs.writeFileSync(outPath, JSON.stringify(playlist, null, 2));
          }
          callback(err, playlist);
        });

      }, callback);
  }, (err, results) => {
    if (err) return printError(err);
    console.log('done');
  });
}
