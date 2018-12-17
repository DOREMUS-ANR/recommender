const fs = require('fs');
const path = require('path');
const moment = require('moment');

const referenceDir = path.join(__dirname, 'references');
const references = [];

const CSVFields = require('./CSVFields.json');

class Record {
  constructor(data) {
    this.id = data.$.recID;

    for (const field of data.FIELD) {
      this.addProperty(field.$.fieldName, field.VALUE, field.$.fieldType);
    }
    // object type 27 == message sonore
    const msRecords = data.OBJECT[0].RECORD;
    const msDescription = msRecords.splice(0, 1)[0].FIELD;

    for (const field of msDescription) {
      this.addProperty(field.$.fieldName, field.VALUE || field, field.$.fieldType);
    }
    // POST PROCESSING
    // interpreter: extract mop
    for (const interpreter of this.getInterpreters()) {
      const note = interpreter.InterventionNote;
      if (!note || !note.includes(' : ')) continue;
      /* eslint-disable prefer-destructuring */
      interpreter.mop = note.split(' : ', 2)[1];
    }

    // AbsoluteScheduledDate and ScheduledTime should be merged
    const date = this.AbsoluteScheduledDate;


    const time = this.ScheduledTime.substring(0, this.ScheduledTime.lastIndexOf(':'));
    this.ScheduledDateTime = moment(`${date}T${time}`).format();
  }

  getInterpreters() {
    if (!this.Interpreter) return [];
    if (!Array.isArray(this.Interpreter)) return [this.Interpreter];
    return this.Interpreter;
  }

  addProperty(prop, value, type = 1) {
    value = Record.parseFieldValue(value, type, prop);

    if (!this[prop]) { // new prop, set it
      this[prop] = value;
    } else if (Array.isArray(this[prop])) { // array, push it
      this[prop].push(value);
    } else { // set to a different type, transform to array
      this[prop] = [this[prop], value];
    }

    return this;
  }

  static get CSVHeader() {
    return CSVFields.map(f => f.label).join(',');
  }

  toCSV() {
    return CSVFields.map(field => field.field.split('+').map((field_) => {
      const [prop, subProp] = field_.split('.', 2);
      if (!Object.hasOwnProperty.call(this, prop)) return '';
      const value = this[prop];
      const valueIsArray = Array.isArray(value);
      if (!subProp) return valueIsArray ? value.join(';') : value;
      return valueIsArray ? value.map(v => v[subProp]).filter(e => !!e).join(';') : value[subProp];
    }).filter(e => !!e).join(';')
      .replace(/[,"\n]/g, '')).join(',');
  }

  static parseFieldValue(value, type, prop) {
    if (Array.isArray(value)) value = value[0];
    type = parseInt(type);
    const obj = {};

    switch (type) {
      case 1: // string
        return value.trim();
      case 2: // date time
        return moment(value, 'DD.MM.YYYY hh:mm:ss').format('YYYY-MM-DD');
      case 4: // int
        return parseInt(value);
      case 5: // int + reference table
        return Record.referenceFor(parseInt(value), prop);
      case 6: // 0/1 for yes/no
        return !!parseInt(value);
      case 7: // float
        return parseFloat(value);
      case 8: // object
        for (const field of value.FIELD) {
          /* eslint-disable max-len */
          obj[field.$.fieldName] = Record.parseFieldValue(field.VALUE, field.$.fieldType, field.$.fieldName);
        }
        return obj;
      default:
        return value;
    }
  }

  static referenceFor(value, prop) {
    const ref = references[prop] || Record.loadReference(prop);
    return ref[value] || value;
  }


  static loadReference(prop) {
    references[prop] = {};
    const referencePath = path.join(referenceDir, `${prop}.json`);
    if (fs.existsSync(referencePath)) references[prop] = JSON.parse(fs.readFileSync(referencePath, 'utf-8'));

    return references[prop];
  }
}

module.exports = Record;
