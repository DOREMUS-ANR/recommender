const SparqlClient = require('sparql-client2');
const levenshtein = require('fast-levenshtein');
const translitterify = require('translitterify');

const debug = false;
var client = new SparqlClient('http://data.doremus.org/sparql');
var catalogs, artists;
const PROPS = [{
  name: 'opus,opusSub',
  weight: 90
}, {
  name: 'orderNum',
  weight: 70
}, {
  name: 'catLabel,catNum',
  weight: 15
}, {
  name: 'key',
  weight: 18
}, {
  name: 'title',
  weight: 10,
  custom: true
}];
module.exports = function(composer, title, cb) {

  getArtists().then(getCatalogs).then(() => {
    if (!composer) return cb();
    // if (composer.toLowerCase() != 'johannes brahms') return cb();

    let compPlain = translitterify(composer).replace('-', ' ');
    let composerUri = artists.find(a => a.label.toLowerCase() == compPlain.toLowerCase());
    if (!composerUri) {
      if(debug) console.warn('\n\nArtist not in the db : ' + composer);
      return cb();
    }
    composerUri = composerUri.uri;

    // extract tokens from title
    let tokens = extractTokens(title, composerUri);
    let sparql = `SELECT DISTINCT * WHERE {
      ?expression mus:U70_has_title ?title.
      OPTIONAL {  ?expression mus:U16_has_catalogue_statement  ?catStat.
                  ?catStat mus:U40_has_catalogue_name / modsrdf:identifier ?catLabel;
                           mus:U41_has_catalogue_number ?catNum
      }

      OPTIONAL { ?expression mus:U10_has_order_number ?orderNum }
      OPTIONAL { ?expression mus:U17_has_opus_statement / mus:U42_has_opus_number ?opus }
      OPTIONAL { ?expression mus:U17_has_opus_statement / mus:U43_has_opus_subnumber ?opusSub }
      OPTIONAL { ?expression mus:U11_has_key / skos:prefLabel ?key }
      ?expCreation efrbroo:R17_created ?expression;
              ecrm:P9_consists_of / ecrm:P14_carried_out_by <${composerUri}> .
    }`;
    // console.log(composer, '|', title);
    sparqlExec(sparql).then((data) => {

      let bindings = data.results.bindings;
      if (!bindings.length) return cb();

      bindings = bindings.map(b => {
        let obj = {};
        Object.keys(b).forEach(p => {
          if (!b.hasOwnProperty(p)) return;
          obj[p] = b[p].value.toLowerCase();
        });
        return obj;
      });
      // console.log(bindings[0]);
      // console.log(tokens);

      let t = tokens;

      bindings.forEach(b => {
        // compute Extended Jaccard Measure (modified)
        let matches = [];
        let shared = [];
        let unique_t = [];
        let unique_b = [];

        PROPS.forEach(prop => {
          if (prop.custom) return;

          let propParts = prop.name.split(',');
          let p = propParts.slice(0, 1);

          if (!t[p]) return; // unique_b.push({ prop, value: 0.2 });
          if (!b[p]) return; // unique_t.push({ prop, value: 0.6 });

          let isDiff = propParts.some(p => t[p] != b[p]); // jshint ignore:line
          if (!isDiff)
            matches.push({
              prop,
              value: 1
            });
          shared.push({
            prop,
            value: 1
          });
        });

        let titleSimilarity = Math.max(
          stringSimilarity(t.title, b.title),
          stringSimilarity(t.title + t.movement, b.title),
          stringSimilarity(t.title.split(',')[0], b.title),
          stringSimilarity(title.split(',')[0], b.title),
          stringSimilarity(title, b.title)
        );
        let titleProp = PROPS.find(p => p.name == 'title');
        matches.push({
          prop: titleProp,
          value: titleSimilarity
        });
        shared.push({
          prop: titleProp,
          value: 1
        });

        let s_match = matches.reduce(weightedSum, 0);
        let s_shared = shared.reduce(weightedSum, 0);
        let s_unique_t = unique_t.reduce(weightedSum, 0);
        let s_unique_b = unique_b.reduce(weightedSum, 0);

        b.score = s_match / (s_shared + s_unique_b + s_unique_t);
        b.matches = matches.map(m => m.value + '|' + m.prop.name);
        b.shared = shared.map(m => m.prop.name);
      });

      bindings.sort((a, b) => b.score - a.score);
      let bests = bindings.slice(0, 3);

      if (debug) {
        console.log('\n\n***', composer, '|', title);
        for (let i of [0, 1, 2]) {
          b = bests[i];
          if (b) {
            console.log(b.score, b.title, b.expression);
            console.log(b.matches, b.shared);
          }
        }
      }
      cb(null, bests);
    }, (err) => {
      handleError(err);
      cb();
    });
  });
};

function extractTokens(title, composerUri) {
  // opus number
  let opus, opusSub;
  let opusRegex = / op[. ] ?(posth|\d+[a-z]*)(?: n[°º](\d+))?/;
  let opusMatch = opusRegex.exec(title);
  if (opusMatch) {
    opus = opusMatch[1];
    opusSub = opusMatch[2];
    title = title.replace(opusMatch[0], '');
  }
  if (opus == 'posth') opus = null;

  // order number
  let orderNum;
  let orderNumRegex = /(?: n(?:[°º]|o\.?) ?(\d+))/;
  let orderNumMatch = orderNumRegex.exec(title);
  if (orderNumMatch) {
    orderNum = orderNumMatch[1];
    title = title.replace(orderNumMatch[0], '');
  }

  // key
  let key;
  let keyRegex = / en (.+ (maj|min))/;
  let engKeyRegex = / in (.+ (maj|min)(or)?)/;
  let keyMatch = keyRegex.exec(title);
  if (keyMatch) {
    key = keyMatch[1]
      .replace('maj', 'majeur')
      .replace('min', 'mineur')
      .replace(/^ut/, 'do');
    title = title.replace(keyMatch[0], '');
  } else {
    keyMatch = engKeyRegex.exec(title);
    if (keyMatch) {
      key = keyMatch[1].replace('-', ' ');
      title = title.replace(keyMatch[0], '');
    }
  }

  // movement
  let movement;
  let mvtRegex = /: (.+)/;
  let mvtMatch = mvtRegex.exec(title);
  if (mvtMatch) {
    movement = mvtMatch[1];
    title = title.replace(mvtMatch[0], '').trim();
  }

  // subtitle (can contain casting!)
  let subtitle;
  let sbtRegex = /- (.+)/;
  let sbtMatch = sbtRegex.exec(title);
  if (sbtMatch) {
    subtitle = sbtMatch[1];
    title = title.replace(sbtMatch[0], '').trim();
  }

  // catalogs
  let catLabel, catNum;
  let catCodes;
  if (composerUri) catObj = catalogs.find(c => c.artist == composerUri);

  if (catObj) {
    let catRegex = new RegExp(` (${catObj.code.join('|')})\.? (.+)`, 'i');
    let catMatch = catRegex.exec(title);
    if (catMatch) {
      catLabel = catMatch[1];
      catNum = catMatch[2].replace(/ pour .+/, '').trim();
      title = title.replace(catMatch[0], '');
    }
  }

  title = title.replace(/, ?$/, '').trim();

  return {
    title,
    opus,
    opusSub,
    orderNum,
    key,
    catLabel,
    catNum,
    movement,
    subtitle
  };

}

function intersection(a, b) {
  return a.filter(el_a =>
    b.some(el_b => el_a == el_b) ? 1 : 0
  );
}

var cache = {};

function sparqlExec(query) {
  return new Promise(function(resolve, reject) {
    if (cache[query]) return resolve(cache[query]);
    // console.log(query);
    client.query(query, function(err, results) {
      if (err) {
        reject(err);
      } else {
        cache[query] = results;
        resolve(results);
      }
    });
  });
}

function getArtists() {
  let sparql = `SELECT DISTINCT ?artist ?name
    WHERE {
     ?artist a ecrm:E21_Person;
          foaf:name ?name .

     ?sth ecrm:P14_carried_out_by ?artist .
    }
    ORDER BY ?artist`;

  return sparqlExec(sparql).then((res) => {
    artists = res && res.results.bindings.map(b => ({
      uri: b.artist.value,
      label: translitterify(b.name.value).replace('-', ' ')
    }));
  });
}

function getCatalogs() {
  let sparql = `SELECT DISTINCT ?subject GROUP_CONCAT(DISTINCT ?id, ',') AS ?ids
      WHERE {
         <http://data.doremus.org/vocabulary/catalog/> <http://www.w3.org/ns/dcat#record> ?cat.
         ?cat modsrdf:identifier ?id;
              dct:subject ?subject .
      }
      GROUP BY ?subject`;

  return sparqlExec(sparql).then((res) => {
    catalogs = res && res.results.bindings.map(b => ({
      artist: b.subject.value,
      code: b.ids.value.split(',')
    }));
  });
}

function stringSimilarity(a, b) {
  return (a.length - levenshtein.get(a, b)) / a.length;
}

function weightedSum(acc, cur) {
  let score = cur.prop.weight * cur.value;
  return acc + score;
}
