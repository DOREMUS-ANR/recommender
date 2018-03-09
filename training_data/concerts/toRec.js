const fs = require('fs-extra');
const path = require('path');
const jsonfile = require('jsonfile');
const SparqlClient = require('virtuoso-sparql-client').Client;
const async = require('async');

var client = new SparqlClient('http://data.doremus.org/sparql');
client.setOptions("application/json");

var input_dir = __dirname;
var out_dir = path.join(__dirname, './output/json/');
var list_dir = path.join(__dirname, './output/list/');
fs.ensureDirSync(out_dir);

const INSTITUTION_LIST = ['Radio_France', 'Philharmonie_de_Paris'];
const QUERY_CONCERTS = fs.readFileSync(path.join(input_dir, '/query_concerts.rq'), 'utf8');
const QUERY_PIECES = fs.readFileSync(path.join(input_dir, '/query_played_expression.rq'), 'utf8');

INSTITUTION_LIST.forEach(run);

function run(institution) {
  var list_dir_artist = path.join(list_dir, institution, 'artist');
  var list_dir_expression = path.join(list_dir, institution, 'expression');
  fs.ensureDirSync(list_dir_artist);
  fs.ensureDirSync(list_dir_expression);

  let inst_uri = `<http://data.doremus.org/organization/${institution}>`;

  let query_concerts = QUERY_CONCERTS.replace('?institution', inst_uri);
  client.query(query_concerts)
    .then(result => result.results.bindings)
    .then(bindings => bindings.map(b => b.s.value))
    .then(concerts_uris =>
      async.mapSeries(concerts_uris, queryForPieces,
        (e, res) => {
          if (e) throw e;
          res.map(manageConcert).forEach(concert => {
            let uuid = concert.id.split('/');
            uuid = uuid[uuid.length - 1];
            console.log(uuid);

            fs.writeFileSync(`${out_dir}/${uuid}.json`, JSON.stringify(concert, null, 2));
            fs.writeFileSync(`${list_dir_artist}/${uuid}.json`,
              concert.expression.map(e => e.composer).join('\n'));
            fs.writeFileSync(`${list_dir_expression}/${uuid}.json`,
              concert.expression.map(e => e.id).join('\n'));
          });
        }
      )
    ).catch(e => console.error(e));
}

async function queryForPieces(concert) {
  return await client.query(QUERY_PIECES.replace('%%uri%%', concert))
    .then(result => result.results.bindings);
}

function manageConcert(json) {
  let expression = json.map(line => ({
    composer: line.composer && line.composer.value,
    id: line.expression.value
  }));
  return {
    id: json[0].concert.value,
    expression
  };
}
