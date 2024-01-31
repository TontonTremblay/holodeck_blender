import json
from openai import OpenAI
client = OpenAI()

# Specify the path to your JSON file
file_path = 'data/example.json'
texture_names = 'texture_classes.txt'
# Open the JSON file and load its contents
with open(file_path, 'r') as json_file:
    data = json.load(json_file)

with open(texture_names, 'r') as txt_file:
    # Use list comprehension to strip newline characters from each line and create a list
    texture_classe = [line.strip() for line in txt_file]
rooms = {}

for iwall, wall in enumerate(data['walls']):
    wall_text_name = wall['material']['name']
    if wall['roomId'] in rooms: 
        data['walls'][iwall]['material']['ambientcg'] = rooms[wall['roomId']]

        continue


    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": f"I have a texture name as {wall_text_name}. I have the following classes of textures {','.join(texture_classe)}, please select the most likely to be what it should be. Only output a single word."
        },
        {
          "role": "user",
          "content": "Please give me a single texture."
        }

      ],
      temperature=0.7,
      max_tokens=64,
      top_p=1
    )
    # Extracting the response from the completion
    texture_response = response.choices[0].message.content
    data['walls'][iwall]['material']['ambientcg'] = texture_response
    # raise()
    rooms[wall['roomId']] = texture_response
for ifloor, floor in enumerate(data['rooms']):
    floor_text_name = floor['floorMaterial']['name']


    response = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {
          "role": "system",
          "content": f"I have a texture name as {floor_text_name}. I have the following classes of textures {','.join(texture_classe)}, please select the most likely to be what it should be. Only output a single word."
        },
        {
          "role": "user",
          "content": "Please give me a single texture."
        }

      ],
      temperature=0.7,
      max_tokens=64,
      top_p=1
    )
    # Extracting the response from the completion
    texture_response = response.choices[0].message.content
    data['rooms'][ifloor]['floorMaterial']['ambientcg'] = texture_response
    # raise()



with open(file_path.replace('.json','_added.json'), 'w') as json_file:
    json.dump(data, json_file)
