import os
import argparse
import objaverse
import multiprocessing
import json 

parser = argparse.ArgumentParser(description='make_scene')
parser.add_argument(
    '--save_file', 
    type=str, 
    default='./scene.blend',
    help='path for saving rendered image'
)
parser.add_argument(
    '--json', 
    type=str, 
    default='./data/example.json',
    help='path for saving rendered image'
)
parser.add_argument(
    '--blender_root', 
    type=str, 
    default='/Applications/Blender.app/Contents/MacOS/Blender',
    help='path to blender executable'
    )
parser.add_argument(
    '--content_folder', 
    type=str, 
    default='./assets/',
    help='path to blender executable'
    )

parser.add_argument(
    '--objaverse_path',
    type=str,
    default='/Users/jtremblay/.objaverse/hf-objaverse-v1/glbs/',
    help='path to where objaverse downloaded stuff -- could be determined automatically'
    )

opt = parser.parse_args()



# since blender python is broken, lets download the objaverse assets first for the file. 
processes = multiprocessing.cpu_count()

with open(opt.json, 'r') as file:
    data = json.load(file)

to_load = []


for obj in data['objects']:
    to_load.append(obj['assetId'])
print(to_load)
print(len(to_load))
print(objaverse.__version__)
# raise()

objects = objaverse.load_objects(
    uids=to_load,
    download_processes=1
)


import glob 

render_cmd = f'{opt.blender_root} -b -P blender/blender.py -- --output {opt.save_file} --json {opt.json} \
                --content {opt.content_folder} --objaverse_path {opt.objaverse_path}' 

# render_cmd = render_cmd + ' > tmp.out'

print(render_cmd)
os.system(render_cmd)


