const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');

var main_dir = path.join(__dirname, './output/playlists/json/');
var out_dir = path.join(__dirname, './output/playlists/rec/');
var list_dir = path.join(__dirname, './output/playlists/list/');
fs.ensureDirSync(out_dir);
fs.ensureDirSync(list_dir);

let expressionScores = [],
  artistScores = [];

fs.readdirSync(main_dir).forEach(file => {
  let pl = jsonfile.readFileSync(main_dir + file);
  let pl_id = pl.id;
  console.log('Loaded ' + pl_id);

  let records = takeDistinctFrom(pl.tracks, r => r.best || r.album);
  expressionScores.push(...scoresFormSet(records));

  let records_artist = takeDistinctFrom(pl.tracks, r => r.composer || (r.artists && r.artists[0]));
  artistScores.push(...scoresFormSet(records_artist));

  // flat list playlist by playlist
  for (let what of ['artist', 'expression']) {

    let list = (what == 'artist') ? records_artist : records;
    list = list.filter(l => l.startsWith('http'));

    if (list.length < 8) continue;

    let folder = path.join(list_dir, what);
    let filename = `${file.replace('.json', '')}.${what}.txt`;

    fs.ensureDirSync(folder);
    fs.writeFileSync(path.join(folder, filename), list.join('\n'));
  }

});

fs.writeFileSync(`${out_dir}/expression.dat`, expressionScores.join('\n'));
fs.writeFileSync(`${out_dir}/artist.dat`, artistScores.join('\n'));
console.log("done");

function takeDistinctFrom(array, mapFn) {
  let results = [],
    prev = null;
  for (let v of array) {
    let value = mapFn(v);
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
  let scores = [];
  let x_max = 30 * 60; // 30 min
  let c = 0.4;
  let a = -c / Math.pow(x_max, 2);
  let sqF = squareFun(a, c);
  for (let i in records) {
    let r = records[i];
    if (notAnUri(r)) continue;

    for (let j in records) {
      if (i <= j) continue;
      let s = records[j];
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
  'use strict';
  return x => (a * Math.pow(x, 2) + b);
}

function notAnUri(input) {
  if (!input) return false;
  return !input.startsWith('http://');
}
// user_id item_id rating timestamp
