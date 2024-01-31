import os
import json
import open3d as o3d
import numpy as np

# Path to the directory containing your JSON files
json_dir = "/Users/jtremblay/Downloads/2024_01_25_19_46_39/"

# List to store camera poses
camera_poses = []

# Iterate through each JSON file in the directory
for filename in os.listdir(json_dir):
    if filename.endswith(".json"):
        file_path = os.path.join(json_dir, filename)
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Assuming 'cameraPoseARFrame' is the key storing camera pose
            # print(data)
            if "cameraPoseARFrame" in data.keys(): 
                camera_pose = data['cameraPoseARFrame']
                camera_pose = np.array(camera_pose).reshape([4,4])
                camera_poses.append(camera_pose)

# Convert camera poses to numpy array
camera_poses = np.array(camera_poses)

# Visualize camera poses
visualizer = o3d.visualization.Visualizer()
visualizer.create_window()

mesh = o3d.io.read_point_cloud(f"{json_dir}/points.ply")
print(mesh)
visualizer.add_geometry(mesh)

# Visualize each camera pose
for pose in camera_poses:
    # Create a sphere to represent the camera pose
    # camera_sphere = o3d.geometry.TriangleMesh.create_sphere(radius=0.1)
    camera_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1, origin=[0, 0, 0])

    # camera_sphere.paint_uniform_color([0.8, 0.2, 0.2])  # Red color

    # Transform the sphere according to the camera pose
    camera_frame.transform(pose)

    # Add the camera sphere to the visualizer
    visualizer.add_geometry(camera_frame)

# Run the visualizer
visualizer.run()
visualizer.destroy_window()
