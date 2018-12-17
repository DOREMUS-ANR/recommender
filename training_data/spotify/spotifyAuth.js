const SpotifyWebApi = require('spotify-web-api-node');
const config = require('./config.json');

// credentials are optional
const spotifyApi = new SpotifyWebApi({
  clientId: config.clientId,
  clientSecret: config.clientSecret,
  redirectUri: 'http://www.example.com/callback',
});


function login(callback = () => {}) {
  // Retrieve an access token
  return spotifyApi.clientCredentialsGrant()
    .then((data) => {
      console.log(`The access token expires in ${data.body.expires_in}`);
      console.log(`The access token is ${data.body.access_token}`);

      // Save the access token so that it's used in future calls
      spotifyApi.setAccessToken(data.body.access_token);

      callback(null, spotifyApi);
      return spotifyApi;
    }).catch((err) => {
      console.error('Something went wrong when retrieving an access token', err.message);
      callback(err);
    });
}

module.exports = { login };
