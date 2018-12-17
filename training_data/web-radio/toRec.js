const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');

const main_dir = path.join(__dirname, './output/json/');
const out_dir = path.join(__dirname, './output/rec/');
const list_dir = path.join(__dirname, './output/list/');
fs.ensureDirSync(out_dir);

const channel = {};
const scores = {
  expression: [],
  artist: []
};

fs.readdirSync(main_dir).forEach(file => {
  // if (!file.includes('FM-401_20171218_00-23')) return;
  const pl = jsonfile.readFileSync(main_dir + file);
  const pl_id = pl.id.replace(/[^\d]/g, '');

  console.log(`Loaded ${pl_id}`);

  const records = takeDistinctFrom(pl.records, r => r.best || r.AlbumTitle);
  scores.expression.push(...scoresFormSet(records));

  const records_artist = takeDistinctFrom(
    pl.records,
    r => r.composer || (r.Compositor && r.Compositor.FullName)
  );
  scores.artist.push(...scoresFormSet(records_artist));

  // flat list playlist by playlist
  for (const what of ['artist', 'expression']) {
    let list = what == 'artist' ? records_artist : records;
    list = list.map(l => l.value).filter(l => l.startsWith('http'));

    if (list.length < 8) {
      if (pl_id.startsWith('401')) console.log('-', what, list.length, file);
      continue;
    }
    const folder = path.join(list_dir, what);
    const filename = `${file.replace('.json', '')}.${what}.txt`;

    fs.ensureDirSync(folder);
    fs.writeFileSync(path.join(folder, filename), list.join('\n'));
  }

  const ch = getChannel(pl.channel);
  ch.expression.push(...records.map(e => e.value).filter(isAnUri));
  ch.artist.push(...records_artist.map(e => e.value).filter(isAnUri));
});

// mix from different channels as negative
const ch_ids = Object.keys(channel);
for (let i = 0; i < 1000; i++) {
  const c1 = randomFrom(ch_ids);
  const c2 = randomFrom(ch_ids.filter(not(c1)));
  const what = randomFrom(['artist', 'expression']);
  const e1 = randomFrom(channel[c1][what]);
  const e2 = randomFrom(channel[c2][what]);
  scores[what].push([e1, e2, 0].join(' '));
}

fs.writeFileSync(`${out_dir}/expression.dat`, scores.expression.join('\n'));
fs.writeFileSync(`${out_dir}/artist.dat`, scores.artist.join('\n'));
console.log('done');

function randomFrom(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function not(x) {
  return y => x !== y;
}

function getChannel(id) {
  // cannels 402 and 401 are too similar, count as 1
  if (id == 402) id = 401;

  channel[id] = channel[id] || {
    expression: [],
    artist: [],
    id
  };
  return channel[id];
}

function takeDistinctFrom(array, mapFn) {
  const results = [];

  let prev = {};
  for (const v of array) {
    const value = mapFn(v);
    if (!value) {
      prev = {};
      continue;
    }

    const start = toSeconds(v.ScheduledTime);
    const duration = toSeconds(v.ScheduledDuration);

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
  const [h, m, s] = string.split(':').map(item => parseInt(item));
  return h * 60 * 60 + m * 60 + s;
}

function scoresFormSet(records) {
  const scores = [];
  const x_max = 30 * 60; // 30 min
  // let c = 0.4;
  const c = 1;
  const a = -c / Math.pow(x_max** 2);
  const sqF = squareFun(a, c);
  for (const i in records) {
    const r = records[i];
    if (notAnUri(r.value)) continue;

    for (const j in records) {
      if (i <= j) continue;
      const s = records[j];
      if (notAnUri(s.value)) continue;

      const time_distance = Math.abs(r.start - s.end);

      if (time_distance > x_max) continue;
      // here I could have take a different choice indeed

      const score = Math.abs(j - i) == 1 ? 1 : sqF(time_distance) + (1 - c);
      scores.push([r.value, s.value, score].join(' '));
    }
  }
  return scores;
}

function toDatLine(record, playlist_id) {
  return [playlist_id, record, 1, 0].join(' ');
}

function squareFun(a, b) {
  // return x => (a * Math.pow(x, 2) + b);
  return x => 1;
}

function notAnUri(input) {
  return !isAnUri(input);
}

function isAnUri(input) {
  return input && input.startsWith('http://');
}
// user_id item_id rating timestamp
