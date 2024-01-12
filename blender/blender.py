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
import bmesh

def create_wall_mesh(name, vertices):
    # Create a new mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name + "_Object", mesh)

    # Link the object to the scene
    scene = bpy.context.scene
    scene.collection.objects.link(obj)

    # Make the new object the active object
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Enter Edit mode to create the wall geometry
    bpy.ops.object.mode_set(mode='EDIT')

    # Create a BMesh
    bm = bmesh.new()

    # Create the vertices
    for v in vertices:
        bm.verts.new(v)

    # Ensure the lookup table is updated
    bm.verts.ensure_lookup_table()


    # Create the edges between consecutive vertices
    for i in range(len(vertices)-1):
        bm.edges.new([bm.verts[i], bm.verts[i+1]])

    # Create the face (assuming a closed loop)
    bm.faces.new(bm.verts)

    bpy.ops.object.mode_set(mode='OBJECT')


    # Update the mesh with the BMesh data
    bm.to_mesh(mesh)
    bm.free()

###################
###################
###################
###################
###################
###################
###################
###################
###################

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


def add_wall(wall):
    wall_vertices = []
    eps = 0.005
    for vert in wall['polygon']:
        wall_vertices.append((vert['x'],vert['z'],vert['y']))
    wall_vertices = np.array(wall_vertices)

    if 'west' in wall['id']:
        wall_vertices[:,0]-=eps
    if 'east' in wall['id']:
        wall_vertices[:,0]+=eps
    if 'north' in wall['id']:
        wall_vertices[:,1]+=eps
    if 'south' in wall['id']:
        wall_vertices[:,1]-=eps

    if 'west' in wall['id'] and 'exterior' in wall['id']:
        wall_vertices[:,0]-=eps*2
    if 'east' in wall['id'] and 'exterior' in wall['id']:
        wall_vertices[:,0]+=eps*2
    if 'north' in wall['id'] and 'exterior' in wall['id']:
        wall_vertices[:,1]+=eps*2
    if 'south' in wall['id'] and 'exterior' in wall['id']:
        wall_vertices[:,1]-=eps*2

    create_wall_mesh(wall['id'],wall_vertices)    


for wall in data['walls']:
    add_wall(wall)

for floor in data['rooms']:
    floor_vertices = []
    for vert in floor['vertices']:
        floor_vertices.append((vert[0],vert[1],0))
    floor_vertices = np.array(floor_vertices)
    create_wall_mesh(floor['id'],floor_vertices)





bpy.ops.wm.save_as_mainfile(filepath=opt.output)