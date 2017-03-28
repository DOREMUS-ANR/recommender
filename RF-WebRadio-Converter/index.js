const fs = require('fs');
const path = require('path');
const async = require('async');
const xml2js = require('xml2js').Parser();
const json2csv = require('json-2-csv').json2csv;

const Record = require('./Record');

let inputPath = path.join(__dirname, 'input');
let outputPath = path.join(__dirname, 'output');

if (!fs.existsSync(outputPath)) fs.mkdirSync(outputPath);
for (let subFolder of ['json', 'csv']) {
  let subpath = path.join(outputPath, subFolder);
  if (!fs.existsSync(subpath)) fs.mkdirSync(subpath);
}

fs.readdirSync(inputPath)
  .forEach((fileName) => {
    if (path.extname(fileName) != '.xml') return console.log('Skipping not xml file: ' + fileName);

    console.log('Parsing file ' + fileName);
    var filePath = path.join(inputPath, fileName);
    parseFile(filePath)
      .then(processData, handleError)
      .then(writeOutput, handleError)
      .then(() => console.log('It\'s saved!'), handleError);
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
    records = records.map((r, index) => {
      printProgress(`... record ${index + 1} / ${records.length}`);
      return new Record(r);
    }).filter((r) => r.SoundId == 'Titre de CD');

    console.log(' ... done');
    fullfilled({
      id: objID,
      records
    });
  });
}

function parseFile(file) {
  return new Promise(function(fullfilled, rejected) {
    fs.readFile(file, (err, data) => {
      if (err) return rejected(err);
      xml2js.parseString(data, (err, json) => {
        if (err) return rejected(err);
        if (!json) return rejected('Empty data');
        fullfilled(json);
      });
    });
  });
}

function writeOutput(json) {
  return new Promise(function(fullfilled, rejected) {
    async.parallel([
      (callback) => {
        let output = path.join(outputPath, 'json', json.id + '.json');
        fs.writeFile(output, JSON.stringify(json, null, 2), callback);
      },
      (callback) => {
        let output = path.join(outputPath, 'csv', json.id + '.csv');
        let csv = Record.CSVHeader;
        for (let r of json.records) csv += '\n' + r.toCSV();
        fs.writeFile(output, csv, callback);
      }
    ], (err, results) => {
      if (err) return rejected(err);
      fullfilled();
    });


  });

}

function handleError(er) {
  console.error(error);
}

function printProgress(progress) {
  process.stdout.clearLine();
  process.stdout.cursorTo(0);
  process.stdout.write(progress);
}
