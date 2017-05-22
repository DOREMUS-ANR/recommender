const SparqlClient = require('sparql-client2');
const levenshtein = require('fast-levenshtein');
const translitterify = require('translitterify');

var client = new SparqlClient('http://data.doremus.org/sparql');
var catalogs, artists;

module.exports = function(record, cb) {
  let title = record.LongTitle.toLowerCase(),
    composer = record.Compositor && record.Compositor.FullName;

  getArtists().then(getCatalogs).then(() => {
    if (!composer) return cb();
    console.log('\n\n***', composer, '|', title);
    let compPlain = translitterify(composer).replace('-', ' ');
    let composerUri = artists.find(a => a.label.toLowerCase() == compPlain.toLowerCase());
    if (!composerUri) {
      console.warn('Artist not in the db');
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
        let score = 0;
        let matches = [];
        if (t.opus) {
          let sameOpus = t.opus == b.opus;
          let sameOpusSub = t.opusSub == t.opusSub;
          if (sameOpus && sameOpusSub) {
            score += 20;
            matches.push('opus');
          }
        }

        if (t.orderNum && t.orderNum == b.orderNum) {
          score += 20;
          matches.push('orderNum');
        }

        if (t.catLabel) {
          let sameCatLabel = t.catLabel == b.catLabel;
          let sameCatNum = t.catNum == b.catNum;
          if (sameCatLabel && sameCatNum) {
            score += 7;

            matches.push('catalog');
          }
        }

        if (t.key && t.key == b.key) {
          score += 5;
          matches.push('key');

        }

        let titleSimilarity = Math.max(
          (t.title.length - levenshtein.get(t.title, b.title)) / t.title.length,
          (title.length - levenshtein.get(title, b.title)) / title.length
        );

        score += titleSimilarity * 10;
        b.score = score;
        b.matches = matches;
        b.titleDiff = titleSimilarity;
        // let full = b.full.value.toLowerCase();
        //
        // let fullMatch = intersection(title.split(' '), full.split(' '));
        // b.matches = fullMatch; // matches in the title counts double
        // b.score = fullMatch.length; // matches in the title counts double
      });

      bindings.sort((a, b) => b.score - a.score);
      let bests = bindings.slice(0, 3);

      // for (let i of [0, 1, 2]) {
      //   b = bests[i];
      //   if (b) {
      //     console.log(b.score, b.title, b.expression);
      //     console.log(b.matches, b.titleDiff);
      //   }
      // }
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
  let opusRegex = / op\.? (posth|\d+[a-z]*)(?: n[°º](\d+))?/;
  let opusMatch = opusRegex.exec(title);
  if (opusMatch) {
    opus = opusMatch[1];
    opusSub = opusMatch[2];
    title = title.replace(opusMatch[0], '');
  }
  if (opus == 'posth') opus = null;

  // order number
  let orderNum;
  let orderNumRegex = /(?: n[°º](\d+))/;
  let orderNumMatch = orderNumRegex.exec(title);
  if (orderNumMatch) {
    orderNum = orderNumMatch[1];
    title = title.replace(orderNumMatch[0], '');
  }

  // key
  let key;
  let keyRegex = / en (.+ (maj|min))/;
  let keyMatch = keyRegex.exec(title);
  if (keyMatch) {
    key = keyMatch[1]
      .replace('maj', 'majeur')
      .replace('min', 'mineur')
      .replace(/^ut/, 'do');
    title = title.replace(keyMatch[0], '');
  }

  // movement
  let movement;
  let mvtRegex = / : (.+)/;
  let mvtMatch = mvtRegex.exec(title);
  if (mvtMatch) {
    movement = mvtMatch[1];
    title = title.replace(mvtMatch[0], '');
  }

  // subtitle (can contain casting!)
  let subtitle;
  let sbtRegex = / - (.+)/;
  let sbtMatch = sbtRegex.exec(title);
  if (sbtMatch) {
    subtitle = sbtMatch[1];
    title = title.replace(sbtMatch[0], '');
  }

  // catalogs
  let catLabel, catNum;
  let catCodes;
  if (composerUri) catObj = catalogs.find(c => c.artist == composerUri);

  if (catObj) {
    let catRegex = new RegExp(` (${catObj.code.join('|')}) (.+)`, 'i');
    let catMatch = catRegex.exec(title);
    if (catMatch) {
      catLabel = catMatch[1];
      catNum = catMatch[2].replace(/ pour .+/, '').trim();
      title = title.replace(catMatch[0], '');
    }
  }

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
