import argparse, sys, os, math, re
import bpy
from mathutils import Vector, Matrix
import mathutils
import numpy as np
import json 
import random 
import glob 
# from PIL import Image
# import png 
import threading

parser = argparse.ArgumentParser(description='Renders given obj file by rotation a camera around it.')

parser.add_argument(
    '--output', 
    type=str, 
    default='/media/jtremblay/bf64b840-723c-4e19-9dbc-f6a092b66406/home/jtremblay/data/shapenet/renders/',
    help='The path the output will be dumped to.'
)
parser.add_argument(
    '--json',
    help='path to the json to load from holodeck'
)


argv = sys.argv[sys.argv.index("--") + 1:]
opt = parser.parse_args(argv)



# Clear existing mesh objects and lights in the scene
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.select_by_type(type='MESH')
bpy.ops.object.delete()

# Create a new empty scene
bpy.ops.scene.new(type='EMPTY')

# Set the new empty scene as the active scene
bpy.context.window.scene = bpy.context.scene

# Update the user interface
bpy.context.view_layer.update()




# load the holodeck scene

with open(opt.json, 'r') as file:
    data = json.load(file)










bpy.ops.wm.save_as_mainfile(filepath=opt.output)