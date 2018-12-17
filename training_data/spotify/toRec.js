const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');

const main_dir = path.join(__dirname, './output/playlists/json/');
const out_dir = path.join(__dirname, './output/playlists/rec/');
const list_dir = path.join(__dirname, './output/playlists/list/');
fs.ensureDirSync(out_dir);
fs.ensureDirSync(list_dir);

const expressionScores = [];


const artistScores = [];

fs.readdirSync(main_dir).forEach((file) => {
  const pl = jsonfile.readFileSync(main_dir + file);
  const pl_id = pl.id;
  const pl_name = pl.name;
  console.log(`Loaded ${pl_id}`);

  const records = takeDistinctFrom(pl.tracks, r => r.best || r.album);
  expressionScores.push(...scoresFormSet(records));

  const records_artist = takeDistinctFrom(pl.tracks, r => r.composer || (r.artists && r.artists[0]));
  artistScores.push(...scoresFormSet(records_artist));

  // flat list playlist by playlist
  for (const what of ['artist', 'expression']) {
    let list = (what == 'artist') ? records_artist : records;
    list = list.filter(l => l.startsWith('http'));

    if (list.length < 8) continue;

    const folder = path.join(list_dir, what);
    const filename = `${file.replace('.json', '')}.${pl_name}.${what}.txt`;

    fs.ensureDirSync(folder);
    fs.writeFileSync(path.join(folder, filename), list.join('\n'));
  }
});

fs.writeFileSync(`${out_dir}/expression.dat`, expressionScores.join('\n'));
fs.writeFileSync(`${out_dir}/artist.dat`, artistScores.join('\n'));
console.log('done');

function takeDistinctFrom(array, mapFn) {
  const results = [];


  let prev = null;
  for (const v of array) {
    const value = mapFn(v);
    if (!value) {
      prev = null;
      continue;
    }

    if (value != prev) {
      prev = value;
      results.push(prev);
    }
  }
  return results;
}

function scoresFormSet(records) {
  const scores = [];
  const x_max = 30 * 60; // 30 min
  const c = 0.4;
  const a = -c / Math.pow(x_max, 2);
  const sqF = squareFun(a, c);
  for (const i in records) {
    const r = records[i];
    if (notAnUri(r)) continue;

    for (const j in records) {
      if (i <= j) continue;
      const s = records[j];
      if (notAnUri(s)) continue;

      scores.push([r, s, 1].join(' '));
    }
  }
  return scores;
}

function toDatLine(record, playlist_id) {
  return [playlist_id, record, 1, 0].join(' ');
}

function squareFun(a, b) {
  return x => (a * Math.pow(x, 2) + b);
}

function notAnUri(input) {
  if (!input) return false;
  return !input.startsWith('http://');
}
// user_id item_id rating timestamp
