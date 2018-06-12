const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');
const toCSV = require('array-to-csv');

var main_dir = path.join(__dirname, './output/json/');
var out_dir = path.join(__dirname, './output/pub/');
fs.ensureDirSync(out_dir);

let playlists = fs.readdirSync(main_dir);

let pl_rows = playlists.map(file => {
  let pl = jsonfile.readFileSync(main_dir + file);
  console.log('Loaded ' + pl.id);
  return pl.records.map(t => [
    pl.id, t.id, (t.PressTitle && t.PressTitle.replace(/"/g, "'")) || '',
    (t.Compositor && t.Compositor.FullName) || '', t.best || '', t.composer || ''
  ]);

});

flatten = pl_rows.reduce((acc, val) => acc.concat(val), []);
flatten.unshift('playlist_id track_id track_title track_composer work_match composer_match'.split(' '))
csv = toCSV(flatten).replace(/data\.doremus\.org/g, 'example.com');

fs.writeFileSync(path.join(out_dir, 'web-radio.csv'), csv);



console.log("done");
