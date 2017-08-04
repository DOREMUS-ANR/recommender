const fs = require('fs');
const jsonfile = require('jsonfile');

var main_dir = 'output/playlists/json/';
var out_dir = 'output/playlists/e2r/';
var dat = [],
  train = [],
  test = [];

fs.readdirSync(main_dir).forEach(file => {
  let pl = jsonfile.readFileSync(main_dir + file);
  let pl_id = pl.id.replace(/[^\d]/g, '');

  console.log('Loaded ' + pl_id);

  let records = Array.from(new Set(pl.tracks.filter(r => r.best).map(r => r.best)));

  let l = records.length;
  let cutTrain = Math.floor(l * 0.8); // 80% train 20% test

  let strings = records.map(r => toDatLine(r, pl_id));
  dat = dat.concat(strings);
  train = train.concat(strings.slice(0, cutTrain));
  test = test.concat(strings.slice(cutTrain));
  console.log('tot', dat.length, 'train', train.length, 'test', test.length);
});


fs.writeFileSync(out_dir + `train.dat`, train.join('\n'));
fs.writeFileSync(out_dir + `test.dat`, test.join('\n'));
fs.writeFileSync(out_dir + `feedback.edgelist`, dat.join('\n').replace(/ 1 0/g, ''));

function toDatLine(record, playlist_id) {
  return [playlist_id, record, 1, 0].join(' ');
}


// user_id item_id rating timestamp
