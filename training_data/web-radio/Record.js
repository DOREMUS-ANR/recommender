const fs = require('fs');
const path = require('path');
const noop = require('node-noop');
const moment = require('moment');

let referenceDir = path.join(__dirname, 'references');
let references = [];

const CSVFields = require('./CSVFields.json');

class Record {
  constructor(data) {
    this.id = data.$.recID;

    for (let field of data.FIELD)
      this.addProperty(field.$.fieldName, field.VALUE, field.$.fieldType);

    // object type 27 == message sonore
    let msRecords = data.OBJECT[0].RECORD;
    let msDescription = msRecords.splice(0, 1)[0].FIELD;

    for (let field of msDescription)
      this.addProperty(field.$.fieldName, field.VALUE || field, field.$.fieldType);

    // POST PROCESSING
    // interpreter: extract mop
    for (let interpreter of this.getInterpreters()) {
      let note = interpreter.InterventionNote;
      if (!note || !note.includes(' : ')) continue;
      interpreter.mop = note.split(' : ', 2)[1];
    }

    // AbsoluteScheduledDate and ScheduledTime should be merged
    let date = this.AbsoluteScheduledDate,
      time = this.ScheduledTime.substring(0, this.ScheduledTime.lastIndexOf(':'));
    this.ScheduledDateTime = moment(`${date}T${time}`).format();
  }

  getInterpreters() {
    if (!this.Interpreter) return [];
    if (!Array.isArray(this.Interpreter)) return [this.Interpreter];
    return this.Interpreter;
  }

  addProperty(prop, value, type = 1) {
    value = parseFieldValue(value, type, prop);

    if (!this[prop]) // new prop, set it
      this[prop] = value;
    else if (Array.isArray(this[prop])) // array, push it
      this[prop].push(value);
    else // set to a different type, transform to array
      this[prop] = [this[prop], value];

    return this;
  }

  static get CSVHeader() {
    return CSVFields.map((f) => f.label).join(',');
  }

  toCSV() {
    return CSVFields.map((field) => {
      return field.field.split('+').map((field) => {
        let [prop, subProp] = field.split('.', 2);
        if (!this.hasOwnProperty(prop)) return '';
        let value = this[prop];
        let valueIsArray = Array.isArray(value);
        if (!subProp) return valueIsArray ? value.join(';') : value;
        return valueIsArray ? value.map((v) => v[subProp]).filter((e) => !!e).join(';') : value[subProp];
      }).filter((e) => !!e).join(';').replace(/[,"\n]/g, '');
    }).join(',');
  }
}

function referenceFor(value, prop) {
  let ref = references[prop] || loadReference(prop);
  return ref[value] || value;
}

function loadReference(prop) {
  references[prop] = {};
  let referencePath = path.join(referenceDir, prop + '.json');
  if (fs.existsSync(referencePath))
    references[prop] = JSON.parse(fs.readFileSync(referencePath, 'utf-8'));

  return references[prop];
}

function parseFieldValue(value, type, prop) {
  if (Array.isArray(value)) value = value[0];
  type = parseInt(type);
  switch (type) {
    case 1: // string
      return value.trim();
    case 2: // date time
      return moment(value, 'DD.MM.YYYY hh:mm:ss').format('YYYY-MM-DD');
    case 4: // int
      return parseInt(value);
    case 5: // int + reference table
      return referenceFor(parseInt(value), prop);
    case 6: // 0/1 for yes/no
      return !!parseInt(value);
    case 7: //float
      return parseFloat(value);
    case 8: // object
      let obj = {};
      for (let field of value.FIELD)
        obj[field.$.fieldName] = parseFieldValue(field.VALUE, field.$.fieldType, field.$.fieldName);
      return obj;
    default:
      return value;
  }
}

module.exports = Record;
