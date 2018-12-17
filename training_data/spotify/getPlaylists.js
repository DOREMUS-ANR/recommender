/** ******************************
 * Retrieve the content of the
 * playlists in config.json
 * and interlink them with DOREMUS
 ******************************** */

const fs = require('fs-extra');
const async = require('async');
const path = require('path');
const Track = require('./Track');
const matcher = require('../matcher.js');
const spotifyAuth = require('./spotifyAuth');
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


const {
  playlists,
  full,
} = config;

let spotifyApi;


const outputPath = path.join(__dirname, 'output/playlists/json/');
fs.ensureDir(outputPath);

function run(api) {
  spotifyApi = api;

  async.mapSeries(playlists, (playlist, callback) => {
    const outPath = path.join(outputPath, `${playlist.id}.json`);

    if (!full && fs.existsSync(outPath)) return callback();

    console.log(playlist.id);

    spotifyApi
      .getPlaylist(playlist.user, playlist.id)
      .then((data) => {
        data = data.body;
        playlist.name = data.name;
        playlist.followers = data.followers.total;

        playlist.tracks = data.tracks.items
          .map(t => new Track(t.track));

        async.eachSeries(playlist.tracks, (r, cb) => {
          const title = r.title.toLowerCase();


          const composer = r.artists[0].toLowerCase();
          matcher(composer, title).then((res) => {
            if (!res) return cb();
            if (res.composerUri) r.composer = res.composerUri;
            const [bests] = res;
            if (bests && bests[0]) {
              const best = bests[0];
              if (best.score >= 0.7) {
                r.best = best.expression;
                r.best_matching_score = best.score.toFixed(2);
              }
            }
            return cb();
          }).catch((err) => {
            cb(err);
          });
        }, (err) => {
          if (err) console.error(err);
          else {
            const matched = playlist.tracks.filter(t => t.best).length;
            playlist.n_matched = matched;
            playlist.n_total = playlist.tracks.length;
            console.log(`Playlist ${playlist.id} "${playlist.name}"
            matched: ${matched}`);
            fs.writeFileSync(outPath, JSON.stringify(playlist, null, 2));
          }
          callback(err, playlist);
        });
      }, callback);
  }, (err) => {
    if (err) throw err;
    console.log('done');
  });
}

spotifyAuth.login()
  .then(run)
  .catch(e => console.error(e));
