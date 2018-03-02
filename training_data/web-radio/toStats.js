const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');

var main_dir = path.join(__dirname, './output/json/');
var out_dir = path.join(__dirname, './output/');
fs.ensureDirSync(out_dir);

var channel = {};
var expressionScores = [],
  artistScores = [];

fs.readdirSync(main_dir).forEach(file => {
  // if (!file.includes('FM-401_20171218_00-23')) return;
  let pl = jsonfile.readFileSync(main_dir + file);
  let pl_id = pl.id.replace(/[^\d]/g, '');
  console.log('Loaded ' + pl_id);

  let works = pl.records.map(r => r.best || r.id);
  let artists = pl.records
    .map(r => r.composer || (r.Compositor && r.Compositor.FullName))
    .filter(r => r);

  let ch = getChannel(pl.channel);
  ch.expression.push(...works);
  ch.artist.push(...artists);
});

for (let ch of Object.keys(channel)) {
  let cur_channel = channel[ch];
  let works = cur_channel.expression,
    artist = Array.from(new Set(cur_channel.artist));

  let works_mapped = works.filter(isAnUri);
  let works_tot = works.length,
    works_mapped_tot = works_mapped.length,
    works_mapped_distinct = (new Set(works_mapped)).size;

  let artist_mapped = artist.filter(isAnUri);
  let artist_tot = artist.length,
    artist_mapped_tot = artist_mapped.length;

  cur_channel.stats = [ch, works_tot, works_mapped_tot, works_mapped_distinct, artist_tot, artist_mapped_tot];
}

var sts = Object.keys(channel).map(c => channel[c].stats);
fs.writeFileSync(`${out_dir}/stats.csv`, sts.join('\n'));
console.log("done");

function randomFrom(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function getChannel(id) {
  channel[id] = channel[id] || {
    expression: [],
    artist: []
  };
  return channel[id];
}

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
  return !isAnUri(input);
}

function isAnUri(input) {
  if (!input) return false;
  return input.startsWith('http://');
}
// user_id item_id rating timestamp
