import os
import argparse

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
opt = parser.parse_args()



# get all the file
import glob 

render_cmd = f'{opt.blender_root} -b -P blender/blender.py -- --output {opt.save_file} --json {opt.json} \
                --content {opt.content_folder}' 

# render_cmd = render_cmd + ' > tmp.out'

print(render_cmd)
os.system(render_cmd)


