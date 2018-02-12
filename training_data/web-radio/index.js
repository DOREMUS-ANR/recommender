const fs = require('fs-extra');
const util = require('util');
const path = require('path');
const async = require('async');
const xml2js = require('xml2js').Parser();
const json2csv = require('json-2-csv').json2csv;
const matcher = require('../matcher');
const Record = require('./Record');
const klawSync = require('klaw-sync');

let inputPath = path.join(__dirname, 'input');
let outputPath = path.join(__dirname, 'output');

if (!fs.existsSync(outputPath)) fs.mkdirSync(outputPath);

for (let subFolder of ['json', 'csv']) {
  let subpath = path.join(outputPath, subFolder);
  if (!fs.existsSync(subpath)) fs.mkdirSync(subpath);
}

let inputFiles = klawSync(inputPath, {
  nodir: true,
  filter: item => path.extname(item.path) == '.xml'
});

async.eachSeries(inputFiles, (item, callback) => {
  let filePath = item.path;

  console.log('Parsing file ' + filePath);
  parseFile(filePath)
    .then(processData)
    .then(postProcessData)
    .then(writeOutput)
    .then(callback)
    .catch((error) => console.error(error));
});

function processData(data) {
  console.log('Processing data');
  return new Promise(function(fullfilled, rejected) {

    let obj = data.OBJECT;
    // objType 6 = "conducteur", i.e. programmation or diffusion
    let objID = obj.$.objID;
    let records = obj.RECORD;

    // the first record contains the description of the collection
    let objDescr = records.splice(0, 1)[0].FIELD;
    let channel = objDescr.find(f => f.$.fieldID == '10526').VALUE[0];
    console.log(channel);
    records = records.map((r, index) => {
      printProgress(`... record ${index + 1} / ${records.length}`);
      return new Record(r);
    }).filter((r) => r.SoundId == 'Titre de CD');

    console.log(' ... done');
    fullfilled({
      id: objID,
      channel,
      records
    });
  });
}

function postProcessData(json) {
  console.log('PostProcessing data');
  return new Promise(function(fullfilled, rejected) {
    let {
      records
    } = json;

    let index = 0;
    async.eachSeries(records, (r, cb) => {
      // printProgress(`... record ${++index} / ${records.length}`);

      let title = r.LongTitle || r.PressTitle,
        composer = r.Compositor && r.Compositor.FullName;

      printProgress(`... record ${++index} / ${records.length}`);

      matcher(composer, title).then(res => {
        if (!res) return cb();
        if (res.composerUri)
          r.composer = res.composerUri;

        let bests = res.bests;
        if (bests && bests[0]) {
          let best = bests[0];
          if (best.score >= 0.7) {
            r.best = best.expression;
            r.best_matching_score = best.score.toFixed(2);
          }
        }
        cb();
      });
    }, () => {
      console.log(' ... done');
      json.total = json.records.length;
      json.matched = json.records.filter(r => r.best).length;
      console.log('Matched: ' + json.matched + "/" + json.total);
      fullfilled(json);
    });
  });
}

function parseFile(file) {
  return fs.readFile(file)
    .then(util.promisify(xml2js.parseString))
    .then(json => {
      if (!json) throw 'Empty data';
      return json;
    });
}

function writeOutput(json) {
  console.log('Writing output');
  let json_output = path.join(outputPath, 'json', json.id + '.json');
  let csv_output = path.join(outputPath, 'csv', json.id + '.csv');

  let csv = 'channel,' + Record.CSVHeader;
  for (let r of json.records) csv += '\n' + json.channel + ',' + r.toCSV();

  return Promise.all([
    fs.writeFile(json_output, JSON.stringify(json, null, 2)),
    fs.writeFile(csv_output, csv)
  ]).then(() => console.log('It\'s saved!'));
}

function printProgress(progress) {
  process.stdout.clearLine();
  process.stdout.cursorTo(0);
  process.stdout.write(progress);
}
