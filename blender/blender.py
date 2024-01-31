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
from mathutils import Vector

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
    return obj 

from bpy_extras.image_utils import load_image




def add_material(obj,path_texture, add_uv = False, material_pos = -1):
    if add_uv:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj

        obj.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Unwrap using Smart UV Project
        bpy.ops.uv.smart_project()
        # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

        # Switch back to Object mode
        bpy.ops.object.mode_set(mode='OBJECT')

    name = path_texture.split("/")[-2]
    bpy.context.view_layer.objects.active = obj

    # Create a new material
    new_material = bpy.data.materials.new(name=f"{obj.name}_Material")
    
    # Link the material to the object
    # print(len(obj.data.materials))
    if material_pos == -1 or len(obj.data.materials) ==0:
        obj.data.materials.clear()

        obj.data.materials.append(new_material)
    else:
        obj.data.materials[material_pos] = new_material

    new_material.use_nodes = True
    node_tree = new_material.node_tree

    # Clear default nodes
    for node in node_tree.nodes:
        node_tree.nodes.remove(node)

    principled_node = node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')

    # Create an image texture node
    image_texture_node = node_tree.nodes.new(type='ShaderNodeTexImage')
    image = load_image(f"{path_texture}/{name}_2K-JPG_Color.jpg", new_material)
    image_texture_node.image = image

    # # normal
    img_normal = load_image(f"{path_texture}/{name}_2K-JPG_NormalGL.jpg", new_material)
    image_texture_node_normal = node_tree.nodes.new(type='ShaderNodeTexImage')
    image_texture_node_normal.image = img_normal    
    image_texture_node_normal.image.colorspace_settings.name = 'Non-Color'

    normal_map_node = node_tree.nodes.new(type='ShaderNodeNormalMap')

    node_tree.links.new(normal_map_node.outputs["Normal"], principled_node.inputs["Normal"])
    node_tree.links.new(image_texture_node_normal.outputs["Color"], normal_map_node.inputs["Color"])


    # rough
    if os.path.exists(f"{path_texture}/{name}_2K-JPG_Roughness.jpg"):
        img_rough = load_image(f"{path_texture}/{name}_2K-JPG_Roughness.jpg",new_material)

        image_texture_node_rough = node_tree.nodes.new(type='ShaderNodeTexImage')
        image_texture_node_rough.image = img_rough    
        image_texture_node_rough.image.colorspace_settings.name = 'Non-Color'

        node_tree.links.new(image_texture_node_rough.outputs["Color"], principled_node.inputs["Roughness"])

    # metal
    if os.path.exists(f"{path_texture}/{name}_2K-JPG_Metalness.jpg"):

        img_metal = load_image(f"{path_texture}/{name}_2K-JPG_Metalness.jpg",new_material)

        image_texture_node_metal = node_tree.nodes.new(type='ShaderNodeTexImage')
        image_texture_node_metal.image = img_metal    
        image_texture_node_metal.image.colorspace_settings.name = 'Non-Color'

        node_tree.links.new(image_texture_node_metal.outputs["Color"], principled_node.inputs["Metallic"])



    # connecting
    node_tree.links.new(image_texture_node.outputs["Color"], principled_node.inputs["Base Color"])
    
    material_output_node = node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    node_tree.links.new(principled_node.outputs["BSDF"], material_output_node.inputs["Surface"])




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

parser.add_argument(
    '--objaverse_path',
    help='objaverse path'
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
        wall_vertices[:,0]+=eps
    if 'east' in wall['id']:
        wall_vertices[:,0]-=eps
    if 'north' in wall['id']:
        wall_vertices[:,1]-=eps
    if 'south' in wall['id']:
        wall_vertices[:,1]+=eps

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

def import_glb(file_path, location=(0, 0, 0), rotation=(0, 0, 0), scale=(0.01, 0.01, 0.01),centering=True):
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
    if centering:
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
    obj = create_wall_mesh(floor['id'],floor_vertices)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Unwrap using Smart UV Project
    bpy.ops.uv.smart_project()
    # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

    # Switch back to Object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    add_material(obj,"assets/textures/Concrete040/")
    # add_material(obj,"assets/textures/WoodSiding008/")


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

    if "door" in entry['id'].lower():

        # load doorway
        if 'double' in entry['assetId'].lower():
            doorways = glob.glob(f"{opt.content}/doors/doorway_double*.glb")
        else:
            doorways = glob.glob(f"{opt.content}/doors/doorway_frame*.glb")

        doorway_path = doorways[np.random.randint(0,len(doorways))]
        asset_loaded = import_glb(doorway_path,location=pos,scale=(0.0102,0.0102,0.0102))

        add_material(asset_loaded,"assets/textures/WoodSiding001/",add_uv =True)


        if rotate:
            bpy.context.view_layer.objects.active = asset_loaded
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Z')


        # door 
        doors = glob.glob(f"{opt.content}/doors/doorway_door*.glb")
        door_path = doors[np.random.randint(0,len(doors))]
        door_loaded = import_glb(door_path,location=(0,0,0),scale=(1,1,1))
        add_material(door_loaded,"assets/textures/WoodSiding002/",add_uv =True)
        door_loaded.parent = asset_loaded

        if rotate:
            bpy.context.view_layer.objects.active = door_loaded
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')
        else:
            bpy.context.view_layer.objects.active = asset_loaded
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis="X")

        bpy.ops.transform.translate(value=(0,0,-0.035))


        if 'double' in entry['assetId'].lower():
            door_loaded_2 = import_glb(door_path,location=(0,0,0),scale=(1,1,1))
            add_material(door_loaded_2,"assets/textures/WoodSiding002/",add_uv =True)
            door_loaded_2.parent = asset_loaded

            if rotate:
                bpy.context.view_layer.objects.active = door_loaded_2
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')

                # TODO make this work when on the other wall 


            else:
                bpy.context.view_layer.objects.active = door_loaded_2
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis="X")
                bpy.ops.transform.resize(value=(-1,1,1))
                bpy.ops.transform.translate(value=(-door_loaded_2.dimensions[0]/2,0,-0.035))

                bpy.ops.object.select_all(action='DESELECT')
                door_loaded.select_set(True)
                bpy.context.view_layer.objects.active = door_loaded
                bpy.ops.transform.translate(value=(door_loaded.dimensions[0]/2,0,0))



        # TO DO ADD OPENING CLOSING THE DOOR. 


        # add the handle 
        handles = glob.glob(f"{opt.content}/doors/doorway_handle*.glb")
        handle_path = handles[np.random.randint(0,len(handles))]
        handle_loaded = import_glb(handle_path,location=(0,0,0),scale=(1,1,1),centering=False)
        add_material(handle_loaded,"assets/textures/PaintedMetal001/",add_uv =True)
        # for handle in handles:
        #     handle_loaded = import_glb(handle,location=(0,0,0),scale=(1,1,1),centering=False)        
        # bpy.ops.wm.save_as_mainfile(filepath=opt.output)

        # raise()
        handle_loaded.parent = door_loaded

        bpy.context.view_layer.objects.active = handle_loaded
        if rotate:
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')
            bpy.ops.transform.translate(value=(0,0.3431,-0.0848))
        else:
            bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X')
            bpy.ops.transform.translate(value=(-0.3431,0,-0.0848))

        if 'double' in entry['assetId'].lower():
            handle_loaded_2 = import_glb(handle_path,location=(0,0,0),scale=(1,1,1),centering=False)
            add_material(handle_loaded_2,"assets/textures/PaintedMetal001/",add_uv =True)
            
            handle_loaded_2.parent = door_loaded_2

            bpy.ops.object.select_all(action='DESELECT')
            handle_loaded_2.select_set(True)

            bpy.context.view_layer.objects.active = handle_loaded_2

            if rotate:
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y')
                bpy.ops.transform.translate(value=(0,0.3431,-0.0848))
            else:
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis='X')
                bpy.ops.transform.translate(value=(0.3431,0,-0.0848))




    else:
        # load the asset
        asset_loaded = import_glb(f"{opt.content}/{entry['id'].split('|')[0]}s/{entry['assetId'].lower()}.glb",
            location=pos)
        add_material(asset_loaded,"assets/textures/Wood080/",add_uv =True,material_pos=0)

        if asset_loaded:
            asset_loaded.name = entry['id']
            if rotate:
                bpy.context.view_layer.objects.active = asset_loaded
                bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Z')

    # bpy.ops.wm.save_as_mainfile(filepath=opt.output)




















# go over the walls and then join the ones that are together. 

# find the rooms: 
rooms = {}

for obj in bpy.context.scene.objects:
    print("Object Name:", obj.name)
    if 'exterior' in obj.name or 'window' in obj.name:
        continue

    if 'wall' in obj.name:
        splitted = obj.name.split("|")
        if not splitted[1] in rooms:
            rooms[splitted[1]] = []
        rooms[splitted[1]].append(obj)

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')

        # Unwrap using Smart UV Project
        bpy.ops.uv.smart_project()
        # bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.001)

        # Switch back to Object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # add_material(obj,"assets/textures/Concrete040/")
        add_material(obj,"assets/textures/WoodSiding008/")


print(rooms.keys())






# 
# 
# 
# 
# 

# for room in rooms.keys():
#     bpy.ops.object.select_all(action='DESELECT')
#     rooms[room][0].select_set(True)
#     # bpy.context.scene.objects.active = rooms[room][0]
#     bpy.context.view_layer.objects.active = rooms[room][0]
#     for i_wall in range(1,len(rooms[room])):
#         obj = rooms[room][i_wall] 
#         obj.select_set(True)
#         bpy.context.view_layer.objects.active = obj
#         bpy.ops.object.join()

#     bpy.ops.object.mode_set(mode='EDIT')
#     bpy.ops.mesh.select_all(action='SELECT')

#     # Unwrap using Smart UV Project
#     bpy.ops.uv.smart_project()
#     bpy.ops.object.mode_set(mode='OBJECT')

    # add_material(obj,"assets/textures/WoodSiding008/")
# raise()
# load and put objaverse object

def find_file_in_path(path, file_name):
    for root, dirs, files in os.walk(path):
        if file_name in files:
            return os.path.join(root, file_name)
    return None


def get_dimensions_with_hierarchy(obj,rot=True):
    # Traverse all children recursively and accumulate dimensions
    # print(obj.name)
    # print(obj.rotation_quaternion.to_matrix())
    dimensions = obj.dimensions

    for child in obj.children:
        child_dimensions = get_dimensions_with_hierarchy(child)
        if rot:
            child_dimensions = obj.rotation_quaternion.to_matrix() @ child_dimensions
        dim = [dimensions.x,dimensions.y,dimensions.z]

        dim[0] = max(dim[0], abs(child_dimensions.x))
        dim[1] = max(dim[1], abs(child_dimensions.y))
        dim[2] = max(dim[2], abs(child_dimensions.z))

        dimensions = Vector(dim)


    return dimensions

with open('data/objaverse_holodeck_database.json', 'r') as file:
    data_holodeck = json.load(file)

def reset_transformations_hierarchy(obj):
    # Reset transform for the current object
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)

    # Recursively reset transform for all children
    for child in obj.children:
        reset_transformations_hierarchy(child)

def load_pickled_3d_asset(file_path):
    import gzip
    import pickle
    # Open the compressed pickled file
    with gzip.open(file_path, 'rb') as f:
        # Load the pickled object
        loaded_object_data = pickle.load(f)

    # Create a new mesh object in Blender
    mesh = bpy.data.meshes.new(name='LoadedMesh')
    obj = bpy.data.objects.new('LoadedObject', mesh)

    # Link the object to the scene
    bpy.context.scene.collection.objects.link(obj)

    # Set the mesh data for the object
    obj.data = mesh

    # Update the mesh with the loaded data
    # print(loaded_object_data.keys())
    # print(loaded_object_data['triangles'])
    # triangles = [vertex_index for face in loaded_object_data['triangles'] for vertex_index in face]
    triangles = np.array(loaded_object_data['triangles']).reshape(-1,3)
    vertices = []

    for v in loaded_object_data['vertices']:
        vertices.append([v['x'],v['z'],v['y']])


    mesh.from_pydata(vertices, [], triangles)

    uvs = []
    for uv in loaded_object_data['uvs']:
        uvs.append([uv['x'],uv['y']]) 

    mesh.update()

    # Ensure UV coordinates are stored
    if not mesh.uv_layers:
        mesh.uv_layers.new(name="UVMap")

    uv_layer = mesh.uv_layers["UVMap"]
    for poly in mesh.polygons:
        for loop_index in poly.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            uv_layer.data[loop_index].uv = uvs[vertex_index]
    

    material = bpy.data.materials.new(name="AlbedoMaterial")
    obj.data.materials.append(material)

    # Assign albedo color to the material
    material.use_nodes = True
    nodes = material.node_tree.nodes
    principled_bsdf = nodes.get("Principled BSDF")

    texture_node = nodes.new(type='ShaderNodeTexImage')

    image_path = f"{'/'.join(file_path.split('/')[:-1])}/albedo.jpg"  # Replace with your image file path

    image = bpy.data.images.load(image_path)

    # Assign the image to the texture node
    texture_node.image = image

    # Connect the texture node to the albedo color
    material.node_tree.links.new(
        texture_node.outputs["Color"],
        principled_bsdf.inputs["Base Color"]
    )


    # normal
    image_path = f"{'/'.join(file_path.split('/')[:-1])}/normal.jpg"
    img_normal = bpy.data.images.load(image_path)
    image_texture_node_normal = material.node_tree.nodes.new(type='ShaderNodeTexImage')
    image_texture_node_normal.image = img_normal    
    image_texture_node_normal.image.colorspace_settings.name = 'Non-Color'

    normal_map_node = material.node_tree.nodes.new(type='ShaderNodeNormalMap')

    material.node_tree.links.new(normal_map_node.outputs["Normal"], principled_bsdf.inputs["Normal"])
    material.node_tree.links.new(image_texture_node_normal.outputs["Color"], normal_map_node.inputs["Color"])





    # Assign the material to the object
    obj.data.materials[0] = material    

    # Update mesh to apply UV changes
    mesh.update()


    # raise()


    # Update other properties as needed
    # obj.location = loaded_object_data['location']
    # obj.rotation_euler = loaded_object_data['rotation']
    # obj.scale = loaded_object_data['scale']

    return obj

# def get_scale_factor(target_size, metadata):
#     if target_size == None: return

#     bounding_box = metadata["assetMetadata"]["boundingBox"]
#     original_size = (abs(bounding_box["max"]["x"] - bounding_box["min"]["x"]) * 100,
#                      abs(bounding_box["max"]["y"] - bounding_box["min"]["y"]) * 100,
#                      abs(bounding_box["max"]["z"] - bounding_box["min"]["z"]) * 100)
    
#     for i in range(3):
#         if original_size[i] == 0:
#             original_size[i] = 1
#     try:    
#         original_size_ordered = sorted(original_size)
#         target_size_ordered = sorted(target_size)

#         scale_factors = [target_size_ordered[i] / original_size_ordered[i] for i in range(3)]
#         scale_factor = np.mean(scale_factors)

#         if scale_factor > 1.3: scale_factor = 1.3
#         elif scale_factor < 1.0: scale_factor = 1.0

#         return scale_factor
    
#     except:
#         return None


# for i_obj, obj in enumerate(data['objects']):
#     file_path = find_file_in_path(opt.objaverse_path,f"{obj['assetId']}.glb")
#     # print(opt.objaverse_path,f"{obj['assetId']}.glb")
#     # break
#     if file_path is None:
#         continue
#     bpy.ops.import_scene.gltf(filepath=file_path)

#     # loaded = load_pickled_3d_asset(f"{opt.objaverse_path}/{obj['assetId']}/{obj['assetId']}.pkl.gz")
#     # bpy.ops.object.select_all(action='DESELECT')
#     # loaded.select_set(True)
#     # bpy.context.view_layer.objects.active = loaded

#     loaded = bpy.context.view_layer.objects.active
#     loaded.select_set(True)
    

#     # bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
#     # reset_transformations_hierarchy(loaded)

#     # if not obj['rotation']['y'] == 0: 
#     #     bpy.ops.transform.rotate(value=math.radians(obj['rotation']['y']), orient_axis='Z')

#     dim = get_dimensions_with_hierarchy(loaded)
#     holo_dim = data_holodeck[obj['assetId']]['assetMetadata']['boundingBox']

#     # scale = dim[0]/holo_dim['x']
#     # bpy.ops.transform.resize(value=[1/scale,1/scale,1/scale])

#     # dim = get_dimensions_with_hierarchy(loaded)

#     # print(dim)

#     loaded.location.x = obj['position']['x']
#     loaded.location.y = obj['position']['z']
#     # loaded.location.z = obj['position']['y']
#     loaded.location.z = dim[2]/2


#     # 7.52757


#     print()

#     if i_obj>9:
#         break
#     # break

for i_obj, obj in enumerate(data['objects']):
    # file_path = find_file_in_path(opt.objaverse_path,f"{obj['assetId']}.glb")
    # print(opt.objaverse_path,f"{obj['assetId']}.glb")
    # break
    # if file_path is None:
    #     continue
    # bpy.ops.import_scene.gltf(filepath=file_path)

    # loaded = bpy.context.view_layer.objects.active
    # loaded.select_set(True)

    if not os.path.exists(f"{opt.objaverse_path}/{obj['assetId']}/{obj['assetId']}.pkl.gz"):
        print(obj['assetId'])
        continue

    loaded = load_pickled_3d_asset(f"{opt.objaverse_path}/{obj['assetId']}/{obj['assetId']}.pkl.gz")
    bpy.ops.object.select_all(action='DESELECT')
    loaded.select_set(True)
    bpy.context.view_layer.objects.active = loaded    

    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN', center='BOUNDS')
    # reset_transformations_hierarchy(loaded)

    if not obj['rotation']['y'] == 0: 
        bpy.ops.transform.rotate(value=math.radians(obj['rotation']['y']), orient_axis='Z')

    dim = get_dimensions_with_hierarchy(loaded)
    holo_dim = data_holodeck[obj['assetId']]['assetMetadata']['boundingBox']

    # scale = dim[0]/holo_dim['x']
    # bpy.ops.transform.resize(value=[1/scale,1/scale,1/scale])

    # dim = get_dimensions_with_hierarchy(loaded)

    # print(dim)

    loaded.location.x = obj['position']['x']
    loaded.location.y = obj['position']['z']
    loaded.location.z = obj['position']['y']
    # loaded.location.z = dim[2]/2


    # 7.52757


    # print()

    # if i_obj>9:
    #     break
    # break


for light in data["proceduralParameters"]['lights']:

    bpy.ops.object.light_add(type='POINT', 
        location=(
            light['position']['x'], 
            light['position']['z'], 
            light['position']['y']
        )
    )

    # Access the newly added light object
    point_light = bpy.context.object

    # Set light properties (optional)
    point_light.data.energy = 400  # Adjust the light intensity



bpy.ops.wm.save_as_mainfile(filepath=opt.output)
