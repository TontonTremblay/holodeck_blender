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
    obj = bpy.data.objects.new(name, mesh)

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

def create_cube(name, min_xyz, max_xyz,location,rotate=False):
    # Calculate dimensions of the cube
    print(min_xyz)
    print(max_xyz)
    dimensions = [max_xyz[i] - min_xyz[i] for i in range(3)]

    # Calculate location of the cube
    # location = [(max_xyz[i] + min_xyz[i]) / 2 for i in range(3)]

    # Create the cube object
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cube = bpy.context.active_object

    # Resize the cube to the specified dimensions
    cube.dimensions = dimensions

    if rotate:
        bpy.context.view_layer.objects.active = cube
        bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Z')


    # cube.location.x += assetPosition[0]
    # cube.location.y += assetPosition[2]
    # cube.location.z += assetPosition[1]
    # Set the cube name
    cube.name = name

    return cube


def find_closest_point(points):
    if not points:
        return None  # Return None if the list is empty

    # Calculate the distance from each point to the origin (0, 0, 0)
    distances = [math.sqrt(p['x']**2 + p['y']**2 + p['z']**2) for p in points]

    # Find the index of the minimum distance
    min_distance_index = distances.index(min(distances))

    # Return the closest point
    return points[min_distance_index]


def subtract_objects(obj_to_subtract, obj_to_subtract_from):

    bpy.context.view_layer.objects.active = obj_to_subtract
    obj_to_subtract.select_set(True)

    mod = obj_to_subtract.modifiers.new("Boolean", type='BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = obj_to_subtract_from

    # large cube has context.
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # context.scene.objects.unlink(obj_to_subtract_from)

#########################
#########################
#########################
#########################
#########################
#########################
#########################



wall_by_id = {}

for wall in data['walls']:
    add_wall(wall)
    wall_by_id[wall['id']]=wall

for floor in data['rooms']:
    floor_vertices = []
    for vert in floor['vertices']:
        floor_vertices.append((vert[0],vert[1],0))
    floor_vertices = np.array(floor_vertices)
    create_wall_mesh(floor['id'],floor_vertices)



for door in data['doors']:
    wall = wall_by_id[door['wall1']]
    eps = 0.1
    pos = find_closest_point(wall['polygon'])

    if 'east' in door['wall0'] or 'west' in door['wall0']:
        asset = create_cube(door['id'],
            [
                door["holePolygon"][0]['z']-eps,
                door["holePolygon"][0]['x'],
                door["holePolygon"][0]['y']
            ],
            [
                door["holePolygon"][1]['z']+eps,
                door["holePolygon"][1]['x'],
                door["holePolygon"][1]['y']
            ],
            [
                door['assetPosition']['z']+pos['x'],
                door['assetPosition']['x']+pos['z'],
                door['assetPosition']['y']+pos['y']
            ],
            # rotate = True
        )
    else:

        asset = create_cube(door['id'],
            [
                door["holePolygon"][0]['x'],
                door["holePolygon"][0]['z']-eps,
                door["holePolygon"][0]['y']
            ],
            [
                door["holePolygon"][1]['x'],
                door["holePolygon"][1]['z']+eps,
                door["holePolygon"][1]['y']
            ],
            [
                door['assetPosition']['x']+pos['x'],
                door['assetPosition']['z']+pos['z'],
                door['assetPosition']['y']+pos['y']
            ]
        )

    # asset.parent = bpy.data.objects[door['wall0']]
    # asset.parent_type = 'OBJECT'
    subtract_objects(bpy.data.objects[door['wall0']],asset)
    subtract_objects(bpy.data.objects[door['wall1']],asset)
    bpy.data.objects.remove(asset)

for window in data['windows']:
    wall = wall_by_id[window['wall1']]
    eps = 0.1
    pos = find_closest_point(wall['polygon'])
    if 'east' in window['wall0'] or 'west' in window['wall0']:
        asset = create_cube(window['id'],
            [
                window["holePolygon"][0]['z']-eps,
                window["holePolygon"][0]['x'],
                window["holePolygon"][0]['y']
            ],
            [
                window["holePolygon"][1]['z']+eps,
                window["holePolygon"][1]['x'],
                window["holePolygon"][1]['y']
            ],
            [
                window['assetPosition']['z']+pos['x'],
                window['assetPosition']['x']+pos['z'],
                window['assetPosition']['y']+pos['y']
            ],
            # rotate = True
        )

    else:
        asset = create_cube(window['id'],
            [
                window["holePolygon"][0]['x'],
                window["holePolygon"][0]['z']-eps,
                window["holePolygon"][0]['y']
            ],
            [
                window["holePolygon"][1]['x'],
                window["holePolygon"][1]['z']+eps,
                window["holePolygon"][1]['y']
            ],
            [
                window['assetPosition']['x']+pos['x'],
                window['assetPosition']['z']+pos['z'],
                window['assetPosition']['y']+pos['y']
            ]
        )
    subtract_objects(bpy.data.objects[window['wall0']],asset)
    subtract_objects(bpy.data.objects[window['wall1']],asset)
    bpy.data.objects.remove(asset)


bpy.ops.wm.save_as_mainfile(filepath=opt.output)
