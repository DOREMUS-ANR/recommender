const fs = require('fs-extra');
const util = require('util');
const path = require('path');
const async = require('async');
const xml2js = require('xml2js').Parser();
const klawSync = require('klaw-sync');
const matcher = require('../matcher');
const Record = require('./Record');

const inputPath = path.join(__dirname, 'input/CONTEMPORAINE/');
const outputPath = path.join(__dirname, 'output');

process.on('unhandledRejection', (reason, p) => {
  console.log('Unhandled Rejection at:', p, 'reason:', reason);
  // application specific logging, throwing an error, or other logic here
});


fs.ensureDirSync(outputPath);
['json', 'csv']
  .map(x => path.join(outputPath, x))
  .forEach(x => fs.ensureDirSync(x));

const inputFiles = klawSync(inputPath, {
  nodir: true,
  traverseAll: true,
  filter: item => path.extname(item.path) === '.xml',
});

function printProgress(progress) {
  process.stdout.clearLine();
  process.stdout.cursorTo(0);
  process.stdout.write(progress);
}

function processData(data) {
  console.log('Processing data');
  return new Promise((fullfilled) => {
    const obj = data.OBJECT;
    // objType 6 = "conducteur", i.e. programmation or diffusion
    const { objID } = obj.$;
    let records = obj.RECORD;

    // the first record contains the description of the collection
    const objDescr = records.splice(0, 1)[0].FIELD;
    const channel = objDescr.find(f => f.$.fieldID === '10526').VALUE[0];
    console.log(channel);
    records = records
      .map((r, index) => {
        printProgress(`... record ${index + 1} / ${records.length}`);
        return new Record(r);
      })
      .filter(r => r.SoundId === 'Titre de CD');

    console.log(' ... done');
    fullfilled({
      id: objID,
      channel,
      records,
    });
  });
}

function postProcessData(json) {
  console.log('PostProcessing data');
  return new Promise((fullfilled, rejected) => {
    const { records } = json;

    let index = 0;
    async.eachSeries(
      records,
      (r, cb) => {
        const title = r.LongTitle || r.PressTitle;

        const composer = r.Compositor && r.Compositor.FullName;

        printProgress(`... record ${++index} / ${records.length}`);

        matcher(composer, title).then((res) => {
          if (!res) return cb();
          if (res.composerUri) r.composer = res.composerUri;
          const { bests } = res;
          if (bests && bests[0]) {
            const best = bests[0];
            if (best.score >= 0.7) {
              r.best = best.expression;
              r.best_matching_score = best.score.toFixed(2);
            }
          }
          return cb();
        }).catch(cb);
      },
      () => {
        console.log(' ... done');
        json.total = json.records.length;
        json.matched = json.records.filter(r => r.best).length;
        console.log(`Matched: ${json.matched}/${json.total}`);
        fullfilled(json);
      }, rejected,
    );
  });
}

function parseFile(file) {
  return fs
    .readFile(file)
    .then(util.promisify(xml2js.parseString))
    .then((json) => {
      if (!json) throw new Error('Empty data');
      return json;
    });
}

function writeOutput(json) {
  console.log('Writing output');
  const jsonOutput = path.join(outputPath, 'json', `${json.id}.json`);
  const csvOutput = path.join(outputPath, 'csv', `${json.id}.csv`);

  let csv = `channel,${Record.CSVHeader}`;
  for (const r of json.records) csv += `\n${json.channel},${r.toCSV()}`;

  return Promise.all([
    fs.writeFile(jsonOutput, JSON.stringify(json, null, 2)),
    fs.writeFile(csvOutput, csv),
  ]).then(() => console.log("It's saved!"));
}

async.eachSeries(inputFiles, (item, callback) => {
  const filePath = item.path;
  console.log(`Parsing file ${filePath}`);
  parseFile(filePath)
    .then(processData)
    .then(postProcessData)
    .then(writeOutput)
    .then(callback)
    .catch(error => console.error(error));
});
