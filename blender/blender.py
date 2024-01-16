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

parser.add_argument(
    '--content',
    help='path to content for loading windows and doors'
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

def import_glb(file_path, location=(0, 0, 0), rotation=(0, 0, 0), scale=(0.01, 0.01, 0.01)):
    if not os.path.exists(file_path):
        return None
    # Import GLB file
    bpy.ops.import_scene.gltf(filepath=file_path)

    # Get the imported object
    imported_object = bpy.context.selected_objects[0]

    # Set the location, rotation, and scale
    # imported_object.location = location
    imported_object.rotation_euler = rotation
    imported_object.scale = scale

    # offset = -imported_object.location
    bpy.context.view_layer.objects.active = imported_object
    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')

    # Apply the offset to keep the specified location
    # imported_object.location += offset
    imported_object.location = location


    return imported_object

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

doors_windows = []
for entry in data['doors']:
    doors_windows.append(entry)

for entry in data['windows']:
    doors_windows.append(entry)

for entry in doors_windows:
    wall = wall_by_id[entry['wall1']]
    eps = 0.1
    pos = find_closest_point(wall['polygon'])
    rotate = False

    if 'east' in entry['wall0'] or 'west' in entry['wall0']:
        pos = [
                entry['assetPosition']['z']+pos['x'],
                entry['assetPosition']['x']+pos['z'],
                entry['assetPosition']['y']+pos['y']
        ]

        asset = create_cube(entry['id'],
            [
                entry["holePolygon"][0]['z']-eps,
                entry["holePolygon"][0]['x'],
                entry["holePolygon"][0]['y']
            ],
            [
                entry["holePolygon"][1]['z']+eps,
                entry["holePolygon"][1]['x'],
                entry["holePolygon"][1]['y']
            ],
            pos
        )

        rotate = True

    else:
        pos = [
                entry['assetPosition']['x']+pos['x'],
                entry['assetPosition']['z']+pos['z'],
                entry['assetPosition']['y']+pos['y']
            ]
        asset = create_cube(entry['id'],
            [
                entry["holePolygon"][0]['x'],
                entry["holePolygon"][0]['z']-eps,
                entry["holePolygon"][0]['y']
            ],
            [
                entry["holePolygon"][1]['x'],
                entry["holePolygon"][1]['z']+eps,
                entry["holePolygon"][1]['y']
            ],
            pos

        )
    for ibj in bpy.data.objects:
        print(ibj.name)
    subtract_objects(bpy.data.objects[entry['wall0']],asset)
    subtract_objects(bpy.data.objects[entry['wall1']],asset)
    bpy.data.objects.remove(asset)

    # load the asset
    asset_loaded = import_glb(f"{opt.content}/{entry['id'].split('|')[0]}s/{entry['assetId'].lower()}.glb",
        location=pos)
    if asset_loaded:
        asset_loaded.name = entry['id']
        if rotate:
            bpy.context.view_layer.objects.active = asset_loaded
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Z')

    # bpy.ops.wm.save_as_mainfile(filepath=opt.output)



bpy.ops.wm.save_as_mainfile(filepath=opt.output)
