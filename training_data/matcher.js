const SparqlClient = require('virtuoso-sparql-client').Client;
const levenshtein = require('fast-levenshtein');
/* eslint-disable import/no-unresolved */
const translitterify = require('translitterify');
const pretry = require('promise.retry');

const debug = false;
const client = new SparqlClient('http://data.doremus.org/sparql');
client.setOptions('application/json');


let catalogs;
let artists;
const PROPS = [{
  name: 'opus,opusSub',
  weight: 90,
},
{
  name: 'orderNum',
  weight: 70,
},
{
  name: 'catLabel,catNum',
  weight: 15,
},
{
  name: 'key',
  weight: 18,
},
{
  name: 'title',
  weight: 10,
  custom: true,
},
];


const cache = {};

function sparqlExec(query) {
  if (cache[query]) return Promise.resolve(cache[query]);

  return client.query(query)
    .then((r) => {
      const result = r && r.results && r.results.bindings;
      cache[query] = result;
      return result || [];
    });
}

async function normalizeUri(uri) {
  const sparql = `SELECT DISTINCT * WHERE { ?s owl:sameAs <${uri}>}`;
  const res = await pretry(() => sparqlExec(sparql), { times: 5 });
  if (!res.length) return uri;
  return res[0].s;
}

function getArtists() {
  const sparql = `SELECT DISTINCT ?artist ?name
    WHERE {
     ?artist a ecrm:E21_Person;
          foaf:name ?name .

     ?sth ecrm:P14_carried_out_by ?artist .
    }
    ORDER BY ?artist`;

  return sparqlExec(sparql).then((res) => {
    artists = res.map(b => ({
      uri: b.artist.value,
      label: translitterify(b.name.value).replace('-', ' '),
    }));
    return artists;
  });
}

function getCatalogs() {
  const sparql = `SELECT DISTINCT ?subject GROUP_CONCAT(DISTINCT ?id, ',') AS ?ids
      WHERE {
         <http://data.doremus.org/vocabulary/catalog/> <http://www.w3.org/ns/dcat#record> ?cat.
         ?cat modsrdf:identifier ?id;
              dct:subject ?subject .
      }
      GROUP BY ?subject`;

  return sparqlExec(sparql).then((res) => {
    catalogs = res.map(b => ({
      artist: b.subject.value,
      code: b.ids.value.split(','),
    }));
    return catalogs;
  });
}

function stringSimilarity(a, b) {
  return (a.length - levenshtein.get(a, b)) / a.length;
}

function weightedSum(acc, cur) {
  const score = cur.prop.weight * cur.value;
  return acc + score;
}

function computeSimilarity(b, t, fullTitle) {
  // compute Extended Jaccard Measure (modified)
  const matches = [];
  const shared = [];
  const uniqueT = [];
  const uniqueB = [];

  PROPS.forEach((prop) => {
    if (prop.custom) return;

    const propParts = prop.name.split(',');
    const p = propParts.slice(0, 1);

    if (!t[p]) return; // uniqueB.push({ prop, value: 0.2 });
    if (!b[p]) return; // uniqueT.push({ prop, value: 0.6 });

    const isDiff = propParts.some(x => t[x] !== b[x]);
    if (!isDiff) {
      matches.push({
        prop,
        value: 1,
      });
    }
    shared.push({
      prop,
      value: 1,
    });
  });

  const titleSimilarity = Math.max(
    stringSimilarity(t.title, b.title),
    stringSimilarity(t.title + t.movement, b.title),
    stringSimilarity(t.title.split(',')[0], b.title),
    stringSimilarity(fullTitle.split(',')[0], b.title),
    stringSimilarity(fullTitle, b.title),
  );
  const titleProp = PROPS.find(p => p.name === 'title');
  matches.push({
    prop: titleProp,
    value: titleSimilarity,
  });
  shared.push({
    prop: titleProp,
    value: 1,
  });

  /* eslint-disable camelcase */
  const s_match = matches.reduce(weightedSum, 0);
  const s_shared = shared.reduce(weightedSum, 0);
  const s_uniqueT = uniqueT.reduce(weightedSum, 0);
  const s_uniqueB = uniqueB.reduce(weightedSum, 0);

  b.score = s_match / (s_shared + s_uniqueB + s_uniqueT);
  b.matches = matches.map(m => `${m.value}|${m.prop.name}`);
  b.shared = shared.map(m => m.prop.name);
}

function extractTokens(title, composerUri) {
  let temp;

  // opus number
  let opus;
  let opusSub;
  const opusRegex = / op[. ] ?(posth|\d+[a-z]*)(?: n[°º](\d+))?/;
  const opusMatch = opusRegex.exec(title);
  if (opusMatch) {
    [temp, opus, opusSub] = opusMatch;
    title = title.replace(temp, '');
  }
  if (opus === 'posth') opus = null;

  // order number
  let orderNum;
  const orderNumRegex = /(?: n(?:[°º]|o\.?) ?(\d+))/;
  const orderNumMatch = orderNumRegex.exec(title);
  if (orderNumMatch) {
    [temp, orderNum] = orderNumMatch;
    title = title.replace(temp, '');
  }

  // key
  let key;
  const keyRegex = / en (.+ (maj|min))/;
  const engKeyRegex = / in (.+ (maj|min)(or)?)/;
  let keyMatch = keyRegex.exec(title);
  if (keyMatch) {
    [temp, key] = keyMatch;
    key = key
      .replace('maj', 'majeur')
      .replace('min', 'mineur')
      .replace(/^ut/, 'do');
    title = title.replace(temp, '');
  } else {
    keyMatch = engKeyRegex.exec(title);
    if (keyMatch) {
      [temp, key] = keyMatch;
      key = key.replace('-', ' ');
      title = title.replace(temp, '');
    }
  }

  // movement
  let movement;
  const mvtRegex = /: (.+)/;
  const mvtMatch = mvtRegex.exec(title);
  if (mvtMatch) {
    [temp, movement] = mvtMatch;
    title = title.replace(temp, '').trim();
  }

  // subtitle (can contain casting!)
  let subtitle;
  const sbtRegex = /- (.+)/;
  const sbtMatch = sbtRegex.exec(title);
  if (sbtMatch) {
    [temp, subtitle] = sbtMatch;
    title = title.replace(temp, '').trim();
  }

  // catalogs
  let catLabel;
  let catNum;
  // let catCodes;
  let catObj;
  if (composerUri) catObj = catalogs.find(c => c.artist === composerUri);

  if (catObj) {
    const catRegex = new RegExp(` (${catObj.code.join('|')})[.]? (.+)`, 'i');
    const catMatch = catRegex.exec(title);
    if (catMatch) {
      [temp, catLabel, catNum] = catMatch;
      catNum = catNum.replace(/ pour .+/, '').trim();
      title = title.replace(temp, '');
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
    subtitle,
  };
}

async function runMatcher(composer, title, n_best = 3) {
  if (!title || !composer) return Promise.resolve(null);
  title = title.toLowerCase();
  const compPlain = translitterify(composer).replace('-', ' ');

  return getArtists()
    .then(getCatalogs)
    .then(() => {
      let composerUri = artists.find(
        a => a.label.toLowerCase() === compPlain.toLowerCase(),
      );
      if (!composerUri) {
        if (debug) console.warn(`\n\nArtist not in the db : ${composer}`);
        return Promise.resolve(null);
      }
      composerUri = composerUri.uri;

      // extract tokens from title
      const tokens = extractTokens(title, composerUri);
      const sparql = `
      SELECT DISTINCT * WHERE {
      ?titleProp rdfs:subPropertyOf dc:title .
      ?expression a efrbroo:F22_Self-Contained_Expression ;
                ?titleProp ?title .
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

      return sparqlExec(sparql)
        .then((bindings) => {
          // console.log(composer, '|', title);
          const output = { composerUri };
          if (!bindings.length) return output;

          bindings = bindings.map((b) => {
            const obj = {};
            Object.keys(b)
              .filter(p => Object.prototype.hasOwnProperty.call(b, p))
              .forEach((p) => {
                obj[p] = b[p].value.toLowerCase();
              });
            return obj;
          });
          // console.log(bindings[0]);
          // console.log(tokens);

          const t = tokens;
          bindings.forEach(b => computeSimilarity(b, t, title));
          bindings.sort((a, b) => b.score - a.score);
          const bests = bindings.slice(0, n_best);

          if (debug) {
            console.log('\n\n***', composer, '|', title);
            /* eslint-disable no-restricted-syntax */
            for (let i = 0; i < bests.length; i++) {
              const b = bests[i];
              console.log(b.score, b.title, b.expression);
              console.log(b.matches, b.shared);
            }
          }

          bests.forEach(async (o) => {
            o.expression = await normalizeUri(o.expression);
          });
          output.bests = bests;
          return output;
        });
    });
}


module.exports = runMatcher;
