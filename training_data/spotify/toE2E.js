const fs = require('fs');
const jsonfile = require('jsonfile');

const main_dir = 'output/playlists/json/';
const out_dir = 'output/playlists/e2e/';
const track_ids = {};
const dataset = {};


let dat = [];


let train = [];


let test = [];

fs.readdirSync(main_dir).forEach((file) => {
  const pl = jsonfile.readFileSync(main_dir + file);
  const pl_id = pl.id.replace(/[^\d]/g, '');

  console.log(`Loaded ${pl_id}`);

  const records = Array.from(new Set(pl.tracks.filter(r => r.best).map(r => r.best)));

  const strings = [];
  for (let i in records) {
    i = Number(i);
    const track1 = records[i];
    if (!track1) continue;

    for (let j = 1 + i; j < records.length; j++) {
      const track2 = records[j];
      if (!track2) continue;

      const distance = j - i;
      const score = Math.max(1, 6 - distance);
      datasetPush(track1, track2);
      datasetPush(track2, track1);
      strings.push(toDatLine(track1, track2, score));
      strings.push(toDatLine(track2, track1, score));
    }
  }
  const l = strings.length;
  const cutTrain = Math.floor(l * 0.8); // 80% train 20% test

  dat = dat.concat(strings);
  train = train.concat(strings.slice(0, cutTrain));
  test = test.concat(strings.slice(cutTrain));
  console.log('tot', dat.length, 'train', train.length, 'test', test.length);
});
// add all other combination to 0
all_tracks = Object.keys(dataset);
console.log(all_tracks.length);
for (let i in all_tracks) {
  i = Number(i);
  t1 = all_tracks[i];
  console.log(t1);
  const dt1 = dataset[t1];
  for (let j = 1 + i; j < all_tracks.length; j++) {
    t2 = all_tracks[j];

    if (t1 == t2) continue;
    if (dt1.includes(t2)) continue;
    decide(0.02, () => {
      dataset[t1].push(t2);
      const dt = toDatLine(t1, t2, 0);
      dat.push(dt);
      decide(0.8, () => {
        train.push(dt);
      }, () => {
        test.push(dt);
      });
    });
  }
}

fs.writeFileSync(`${out_dir}train.dat`, train.sort().join('\n'));
fs.writeFileSync(`${out_dir}test.dat`, test.sort().join('\n'));
fs.writeFileSync(`${out_dir}feedback.edgelist`, dat.sort().join('\n').replace(/ \d 0/g, ''));
// fs.writeFileSync(out_dir + `metadata.tsv`, Object.keys(track_ids).map(k => `${track_ids[k]}\t${k}`).join("\n"));


function decide(prob, success, fail = () => {}) {
  const num = Math.random();
  return num <= prob ? success() : fail();
}

function datasetPush(track1, track2) {
  if (!dataset[track1]) dataset[track1] = [];
  dataset[track1].push(track2);
}

function toDatLine(track1, track2, score = 1) {
  return [track1, track2, score, 0].join(' ');
}

function getTid(track) {
  if (track_ids[track]) return track_ids[track];

  const tid = Object.keys(track_ids).length;
  track_ids[track] = tid;
  return tid;
}

// user_id item_id rating timestamp
