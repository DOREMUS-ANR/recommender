const fs = require('fs');
const path = require('path');
const TSV = require('tsv');

var folder = 'output/playlists';
fs.readdir(folder, (err, files) => {
  if (err)
    return console.error("Could not list the directory.", err);

  var table = [];
  files.forEach((file, index) => {
    // Make one pass and make the file complete
    var filePath = path.join(folder, file);

    var json = JSON.parse(fs.readFileSync(filePath));

    table.push({
      user: json.user,
      id: json.id,
      name: json.name,
      n_total: json.n_total,
      n_matched: json.n_matched,
      followers: json.followers
    });
  });

  let total = table.reduce((acc, cur) => {
    acc.n_total += cur.n_total;
    acc.n_matched += cur.n_matched;
    return acc;
  }, {
    user: 'TOTAL',
    id: 'TOTAL',
    name: 'TOTAL',
    n_total: 0,
    n_matched: 0,
    followers: 'n.a.'
  });
  table.push(total);

  fs.writeFileSync('output/stats.tsv', TSV.stringify(table));

});
