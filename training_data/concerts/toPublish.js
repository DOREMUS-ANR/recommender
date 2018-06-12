const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');
const toCSV = require('array-to-csv');

var main_dir = path.join(__dirname, './output/json/');
var out_dir = path.join(__dirname, './output/pub/');
var emb_dir = '/Users/pasquale/git/music-embeddings';
fs.ensureDirSync(out_dir);

const INSTITUTION_LIST = ['itema3', 'euterpe', 'philharmonie'];

console.log('reading emb files');
var work_uris = fs.readFileSync(path.join(emb_dir, 'expression.emb.u'), 'utf-8').split('\n');
var work_labels = fs.readFileSync(path.join(emb_dir, 'expression.emb.l'), 'utf-8').split('\n');
var artist_uris = fs.readFileSync(path.join(emb_dir, 'artist.emb.u'), 'utf-8').split('\n');
var artist_labels = fs.readFileSync(path.join(emb_dir, 'artist.emb.l'), 'utf-8').split('\n');

INSTITUTION_LIST.forEach(run);

function getLabel(uri) {
  if (!uri) return '';
  let i;
  if (uri.includes('artist')) {
    i = artist_uris.indexOf(uri);
    return i == -1 ? '' : artist_labels[i];
  }

  i = work_uris.indexOf(uri);
  return i == -1 ? '' : work_labels[i];
}

function run(institution) {
  let playlists = fs.readdirSync(path.join(main_dir, institution));

  let pl_rows = playlists.map(file => {
    let pl = jsonfile.readFileSync(path.join(main_dir, institution, file));
    console.log('Loaded ' + pl.id);

    return pl.expression.map(t => [
      pl.id, t.id, getLabel(t.id), t.composer, getLabel(t.composer)
    ]);

  });

  flatten = pl_rows.reduce((acc, val) => acc.concat(val), []);
  flatten.unshift('playlist_id track_id track_title composer_id composer_label'.split(' '));
  csv = toCSV(flatten).replace(/data\.doremus\.org/g, 'example.com');

  fs.writeFileSync(path.join(out_dir, `${institution}_concerts.csv`), csv);
}

console.log("done");
