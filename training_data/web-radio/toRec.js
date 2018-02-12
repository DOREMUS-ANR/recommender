const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');

var main_dir = path.join(__dirname, './output/json/');
var out_dir = path.join(__dirname, './output/rec/');
fs.ensureDirSync(out_dir);

let expressionScores = [],
  artistScores = [];

fs.readdirSync(main_dir).forEach(file => {
  // if (!file.includes('FM-401_20171218_00-23')) return;
  let pl = jsonfile.readFileSync(main_dir + file);
  let pl_id = pl.id.replace(/[^\d]/g, '');

  console.log('Loaded ' + pl_id);

  let records = takeDistinctFrom(pl.records, r => r.best || r.AlbumTitle);
  expressionScores.push(...scoresFormSet(records));

  let records_artist = takeDistinctFrom(pl.records,
    r => r.composer || (r.Compositor && r.Compositor.FullName));
  artistScores.push(...scoresFormSet(records_artist));
});

fs.writeFileSync(`${out_dir}/expression.dat`, expressionScores.join('\n'));
fs.writeFileSync(`${out_dir}/artist.dat`, artistScores.join('\n'));
console.log("done");

function takeDistinctFrom(array, mapFn) {
  let results = [],
    prev = {};
  for (let v of array) {
    let value = mapFn(v);
    if (!value) {
      prev = {};
      continue;
    }

    let start = toSeconds(v.ScheduledTime);
    let duration = toSeconds(v.ScheduledDuration);

    if (value != prev.value) {
      prev = {
        value,
        start,
        end: start + duration
      };
      results.push(prev);
    } else prev.end += duration;
  }
  return results;
}

function toSeconds(string) {
  let [h, m, s] = string.split(':').map(item => parseInt(item));
  return h * 60 * 60 + m * 60 + s;
}

function scoresFormSet(records) {
  let scores = [];
  let x_max = 30 * 60; // 30 min
  let c = 0.4;
  let a = -c / Math.pow(x_max, 2);
  let sqF = squareFun(a, c);
  for (let i in records) {
    let r = records[i];
    if (notAnUri(r.value)) continue;

    for (let j in records) {
      if (i <= j) continue;
      let s = records[j];
      if (notAnUri(s.value)) continue;

      let time_distance = Math.abs(r.start - s.end);

      if (time_distance > x_max) continue;
      // here I could have take a different choice indeed

      let score = (Math.abs(j - i) == 1) ? 1 : sqF(time_distance) + (1 - c);
      scores.push([r.value, s.value, score].join(' '));
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
  return !input.startsWith('http://');
}
// user_id item_id rating timestamp
