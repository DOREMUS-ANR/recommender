const config = require('./config.json'),
  SpotifyWebApi = require('spotify-web-api-node'),
  noop = require('noop');

// credentials are optional
const spotifyApi = new SpotifyWebApi({
  clientId: config.clientId,
  clientSecret: config.clientSecret,
  redirectUri: 'http://www.example.com/callback'
});

module.exports = {
  login
};

function login(callback = noop) {
  // Retrieve an access token
  spotifyApi.clientCredentialsGrant()
    .then((data) => {
      console.log('The access token expires in ' + data.body.expires_in);
      console.log('The access token is ' + data.body.access_token);

      // Save the access token so that it's used in future calls
      spotifyApi.setAccessToken(data.body.access_token);

      callback(null, spotifyApi);
    }, (err) => {
      console.error('Something went wrong when retrieving an access token', err.message);
      callback(err);
    });
}
