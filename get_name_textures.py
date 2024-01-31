import os

# Define the path to the folder containing the subfolders
folder_path = "assets/textures/"

# Get a list of all subfolders
subfolders = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]

# Create a set to store unique names without digits
unique_names = set()

# Iterate through each subfolder
for folder in subfolders:
    # Remove digits from the folder name
    name_without_digits = ''.join(filter(str.isalpha, folder))
    if name_without_digits[-1].isupper():
        name_without_digits = name_without_digits[:-1]
    # Add the name without digits to the set
    unique_names.add(name_without_digits)

# Print the unique names
output_file_path = "texture_classes.txt"

# Write unique names to the text file
with open(output_file_path, 'w') as file:
    for name in sorted(unique_names):
        file.write(name + '\n')

print("Unique names saved to", output_file_path)