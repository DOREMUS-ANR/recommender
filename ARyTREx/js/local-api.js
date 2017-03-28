var localProxyApi = function (serverBasePath) {

  var getArtistRelatedArtists = function(artistId) {
    var url = serverBasePath + '/spotify/artists/' + artistId + '/related-artists';
    return $.ajax({
        url: url
    })
  };

  var getArtistTopTracks = function(artistId, country) {
    var url = serverBasePath + '/spotify/artists/' + artistId + '/top-tracks';
    return $.ajax({
        url: url,
        data: {
            country: country
        }
    })
  };

  var getArtist = function(artistId) {
    var url = serverBasePath + '/spotify/artists/' + artistId;
    return $.ajax({
        url: url
    })
  };

  var getAlbum = function(albumId) {
    var url = serverBasePath + '/spotify/album/' + albumId;
    return $.ajax({
        url: url
    })
  };

  var getArtists = function(artistIds) {
    var url = serverBasePath + '/spotify/artists?ids=' + artistIds;
    return $.ajax({
        url: url
    })
  };

  var searchArtists = function(q, params) {
    var url = serverBasePath + '/spotify/search';
    var data = params
    data['q'] = q
    data['type'] = 'artist'

    return $.ajax({
        url: url,
        data: data
    })
  };

  var searchTracks = function(q, params) {
    var url = serverBasePath + '/spotify/search';
    var data = params
    data['q'] = q
    data['type'] = 'track'

    return $.ajax({
        url: url,
        data: data
    })
  };

  var getTrack = function(trackId) {
    var url = serverBasePath + '/spotify/tracks/' + trackId;
    var url = "https://api.spotify.com/v1/tracks/" + trackId;
    return $.ajax({
        url: url
    })
  };

  var getRecommendationTracks = function(trackId, limit) {
      var url = serverBasePath + '/spotify/recommendations/' + trackId;
      return $.ajax({
          url: url
      })
    /*https://developer.spotify.com/web-api/console/get-recommendations/*/
    // var url = "https://api.spotify.com/v1/tracks/" + trackId;
    // var url = "https://api.spotify.com/v1/recommendations?limit=" + limit + "&seed_tracks=" + trackId;
    // return $.ajax({
    //     url: url,
    //     headers: {
    //       'Authorization': 'Bearer BQArr9G-sIznAQQRl9_KvlHLcdsWAxkAtDPzkvY9L8Udd95F73feaEjILCb-2x_Da8hw8N5aUwCvdQw9mVxDJDClt6c9XgCcv6ue0CLtIu-LSLXDZCa7C80T9ke4XBbmZd2JW8jd'
    //     }
    // })
  };

  var getDeezer = function(deezer) {
    var url = deezer;
    return $.ajax({
        url: url
    })
  };

  return {
    getArtistRelatedArtists: getArtistRelatedArtists,
    getArtist: getArtist,
    getArtists: getArtists,
    searchArtists: searchArtists,
    getArtistTopTracks: getArtistTopTracks,
    getRecommendationTracks: getRecommendationTracks,
    getTrack: getTrack,
    getAlbum: getAlbum,
    searchTracks: searchTracks,
    getDeezer: getDeezer
  }

};
