class Track {
  constructor(trackObj) {
    this.artists = trackObj.artists.map(a => a.name);

    this.title = trackObj.name;
    // sometimes the composer is in the title
    // i.e. "wagner: tannhäuser"
    let titleParts = this.title.split(':', 2);
    let comp = titleParts[0].trim();
    if (this.artists[0].toLowerCase().includes(comp.toLowerCase()))
      this.title = titleParts[1].trim();

    this.album = trackObj.album.name;
    this.id = trackObj.id;
    this.trackNum = trackObj.track_number;
  }
}

module.exports = Track;
