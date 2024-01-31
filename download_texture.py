import pandas as pd

# Replace 'file_path.csv' with the actual path to your CSV file
df = pd.read_csv('assets/ambientCG_downloads_csv.csv')

# Display the first few rows of the DataFrame to verify the data has been loaded successfully
# print(df['downloadAttribute'].unique())

df = df.dropna(subset=['downloadAttribute'])
filtered_df = df[df['downloadAttribute'].str.contains('2K-JPG')]

# print(filtered_df)


import requests
import os
import zipfile 

# Function to download file from URL
def download_file(url, destination):
    response = requests.get(url)
    if response.status_code == 200:
        with open(destination, 'wb') as f:
            f.write(response.content)
        print(f"File downloaded successfully: {destination}")
    else:
        print(f"Failed to download file from {url}")

for index, row in filtered_df.iterrows():
    print(row)
    print(row['downloadLink'])
    zip_file_path = f"assets/textures/{row['assetId']}.zip"
    destination_folder = f"assets/textures/{row['assetId']}/"
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    else:
        continue

    download_file(row['downloadLink'],zip_file_path)
    # Open the zip file for reading
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Extract all the contents of the zip file into the destination folder
        zip_ref.extractall(destination_folder)
    os.remove(zip_file_path)

    # break
