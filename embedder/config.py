import json
from types import SimpleNamespace

with open('config.json') as json_data_file:
    config = json.load(json_data_file)

if type(config) == dict:
    config = SimpleNamespace(**config)
