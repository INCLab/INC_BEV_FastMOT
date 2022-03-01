import json

with open('data/local.json') as f:
    json_data = json.load(f)

print(json_data['resize_to'])