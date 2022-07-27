import os

root_path = os.getcwd()
file_list = os.listdir(root_path)

for file in file_list:
    if 'cpython-310' in file:
        os.rename(os.path.join(root_path, file), os.path.join(root_path, file.replace('cpython-310.', '')))
