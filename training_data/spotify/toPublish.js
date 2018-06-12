const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');
const toCSV = require('array-to-csv');

var main_dir = path.join(__dirname, './output/playlists/json/');
var out_dir = path.join(__dirname, './output/playlists/pub/');
fs.ensureDirSync(out_dir);

let playlists = fs.readdirSync(main_dir);

let pl_rows = playlists.map(file => {
  let pl = jsonfile.readFileSync(main_dir + file);
  console.log('Loaded ' + pl.id);

  return pl.tracks.map(t => [
    pl.id, pl.name, t.id, t.title.replace(/"/g, "'"), t.artists[0], t.best || '', t.composer || ''
  ]);

});

flatten = pl_rows.reduce((acc, val) => acc.concat(val), []);
flatten.unshift('playlist_id playlist_name track_id track_title track_composer work_match composer_match'.split(' '))
csv = toCSV(flatten).replace(/data\.doremus\.org/g, 'example.com');

fs.writeFileSync(path.join(out_dir, 'spotify_playlists.csv'), csv);



console.log("done");
