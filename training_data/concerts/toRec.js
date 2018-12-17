const fs = require('fs-extra');
const path = require('path');
const SparqlClient = require('virtuoso-sparql-client').Client;
const async = require('async');

const client = new SparqlClient('http://data.doremus.org/sparql');
client.setOptions('application/json');

const inputDir = __dirname;
const outDir = path.join(__dirname, './output/json/');
const listDir = path.join(__dirname, './output/list/');
fs.ensureDirSync(outDir);

const INSTITUTION_LIST = [
  'itema3',
  'euterpe',
  'philharmonie',
  'diabolo',
  'bnfbib'
];
const QUERY_CONCERTS = fs.readFileSync(
  path.join(inputDir, '/query_concerts.rq'),
  'utf8'
);
const QUERY_PIECES = fs.readFileSync(
  path.join(inputDir, '/query_played_expression.rq'),
  'utf8'
);

async function queryForPieces(concert) {
  return client
    .query(QUERY_PIECES.replace('%%uri%%', concert))
    .then(result => result.results.bindings);
}

function manageConcert(json) {
  const expression = json.map(line => ({
    composer: line.composer && line.composer.value,
    id: line.expression.value
  }));
  return {
    id: json[0].concert.value,
    expression
  };
}

function unique(input) {
  return input.filter((v, i, a) => a.indexOf(v) === i);
}

function run(institution) {
  const listDirArtist = path.join(listDir, institution, 'artist');
  const listDirExpression = path.join(listDir, institution, 'expression');
  const outDirInst = path.join(outDir, institution);
  fs.ensureDirSync(listDirArtist);
  fs.ensureDirSync(listDirExpression);
  fs.ensureDirSync(outDirInst);

  const graph = `<http://data.doremus.org/${institution}>`;

  const queryConcerts = QUERY_CONCERTS.replace('?g', graph);
  client
    .query(queryConcerts)
    .then(result => result.results.bindings)
    .then(bindings => bindings.map(b => b.s.value))
    .then(concertsUris =>
      async.mapSeries(concertsUris, queryForPieces, (e, res) => {
        if (e) throw e;
        res.map(manageConcert).forEach(concert => {
          let uuid = concert.id.split('/');
          uuid = uuid[uuid.length - 1];
          console.log(uuid);

          fs.writeFileSync(
            `${outDirInst}/${uuid}.json`,
            JSON.stringify(concert, null, 2)
          );
          fs.writeFileSync(
            `${listDirArtist}/${uuid}.json`,
            unique(concert.expression.map(ex => ex.composer)).join('\n')
          );
          fs.writeFileSync(
            `${listDirExpression}/${uuid}.json`,
            unique(concert.expression.map(ex => ex.id)).join('\n')
          );
        });
      })
    )
    .catch(e => console.error(e));
}

INSTITUTION_LIST.forEach(run);
