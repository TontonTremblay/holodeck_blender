import bpy
import os


def set_white_material_to_all(material_name):
    # Check if the material exists
    if material_name not in bpy.data.materials:
        print(f"Material '{material_name}' not found.")
        return

    # Create a new frame material
    frame_material = bpy.data.materials.new(name="Frame_Material")
    frame_material.use_nodes = True
    nodes = frame_material.node_tree.nodes

    # Clear all nodes to start clean
    for node in nodes:
        nodes.remove(node)

    # Create Principled BSDF node
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.location = 0, 0

    # Adjust settings for a common door/window frame material (white)
    node_principled.inputs['Base Color'].default_value = (1, 1, 1, 1)  # White color
    node_principled.inputs['Roughness'].default_value = 0.5  # Non-glossy, slightly rough
    node_principled.inputs['Metallic'].default_value = 0.0  # Non-metallic
    node_principled.inputs['Specular IOR Level'].default_value = 0.5  # Standard specular reflection

    # Create Output node
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 200, 0

    # Link Principled BSDF to Output
    links = frame_material.node_tree.links
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

    # Replace the specified material with the new frame material on all objects
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            if slot.material and slot.material.name == material_name:
                slot.material = frame_material


def set_metal_material_to_all(material_name):
    # Check if the material exists
    if material_name not in bpy.data.materials:
        print(f"Material '{material_name}' not found.")
        return

    # Create a new metal material
    metal_material = bpy.data.materials.new(name="Metal_Material")
    metal_material.use_nodes = True
    nodes = metal_material.node_tree.nodes

    # Clear all nodes to start clean
    for node in nodes:
        nodes.remove(node)

    # Create Principled BSDF node
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.location = 0, 0

    # Adjust settings for metal
    node_principled.inputs['Metallic'].default_value = 1.0  # Full metalness
    node_principled.inputs['Roughness'].default_value = 0.3  # Somewhat polished metal
    node_principled.inputs['Specular IOR Level'].default_value = 0.5  # Standard specular reflection

    # Optionally, adjust base color to simulate different types of metal
    node_principled.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1)  # Silver/Steel color

    # Create Output node
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 200, 0

    # Link Principled BSDF to Output
    links = metal_material.node_tree.links
    links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

    # Replace the specified material with the new metal material on all objects
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            if slot.material and slot.material.name == material_name:
                slot.material = metal_material


def set_glass_material_to_all(material_name):
    # Check if the material exists
    if material_name not in bpy.data.materials:
        print(f"Material '{material_name}' not found.")
        return

    # Create a new glass material
    glass_material = bpy.data.materials.new(name="Glass_Material")
    glass_material.use_nodes = True
    nodes = glass_material.node_tree.nodes

    # Clear all nodes to start clean
    for node in nodes:
        nodes.remove(node)

    # Create Principled BSDF node
    node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    node_principled.location = 0, 0

    # Adjust settings for slightly opaque glass
    node_principled.inputs['Transmission Weight'].default_value = 1.0
    node_principled.inputs['Roughness'].default_value = 0.1  # Slightly opaque
    node_principled.inputs['IOR'].default_value = 1.45

    # Create Output node
    node_output = nodes.new(type='ShaderNodeOutputMaterial')
    node_output.location = 200, 0

    # Link Principled BSDF to Output
    links = glass_material.node_tree.links
    link = links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

    # Iterate over all objects and replace the specified material
    for obj in bpy.data.objects:
        if obj.type == 'MESH':  # Only consider mesh objects
            for slot in obj.material_slots:
                if slot.material and slot.material.name == material_name:
                    slot.material = glass_material


# Example usage
def export_objects(obj, export_directory, prefix="doorway_"):
    """
    Export the given object and its children recursively.
    """
    print(obj.name)
    if obj.name.startswith(prefix):
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')

        # Select the object
        obj.select_set(True)

        # Set as the active object
        bpy.context.view_layer.objects.active = obj

        export_path = os.path.join(export_directory, f"{obj.name}.gltf")
         # Export settings
        export_settings = {
            "filepath": export_path,
            "use_selection": True,  # Export only selected objects
        }

        # Export the object as .gltf
        bpy.ops.export_scene.gltf(**export_settings)

    # Recursively export child objects
    #for child in obj.children:
    #    export_objects(child, export_directory)


if __name__ == "__main__":
    preprocess_door = False
    preprocess_window = True

    if preprocess_door:
        fbx_file_path = './doors/doorways_grp.fbx'
        # Directory to save the exported .gltf files
        export_directory = './doors'

        print('importing the fbx file ...')
        # Import the .fbx file
        bpy.ops.import_scene.fbx(filepath=fbx_file_path)

        # Replace 'doorway_tertiary_mat' with the new glass material in all objects
        set_white_material_to_all("doorway_primary_mat")
        set_metal_material_to_all("doorway_secondary_mat")
        set_glass_material_to_all("doorway_tertiary_mat")

        # Iterate through all objects and export recursively
        for obj in bpy.context.scene.objects:
            export_objects(obj, export_directory, prefix="doorway_")

    if preprocess_window:
        # File path for the .fbx file
        fbx_file_path = './windows/MT_windows_grp.fbx'
        # Directory to save the exported .gltf files
        export_directory = './windows'

        print('importing the fbx file ...')
        # Import the .fbx file
        bpy.ops.import_scene.fbx(filepath=fbx_file_path)

        # Replace 'doorway_tertiary_mat' with the new glass material in all objects
        set_white_material_to_all("window_primary_mat")
        set_glass_material_to_all("window_secondary_mat")
        set_metal_material_to_all("window_tertiary_mat")

        # Iterate through all objects and export recursively
        for obj in bpy.context.scene.objects:
            export_objects(obj, export_directory, prefix="window_")
