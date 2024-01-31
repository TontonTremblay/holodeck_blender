import json

# Specify the path to your JSON file
file_path = 'data/example.json'

# Open the JSON file and load its contents
with open(file_path, 'r') as json_file:
    data = json.load(json_file)