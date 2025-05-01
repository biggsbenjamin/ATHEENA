import os
import numpy as np

import pandas as pd
import glob

# Path to the folder containing files
folder_path = './'

TYPES=['lut','ff','bram','dsp']
# List to store file contents
file_contents = []
tmp_dict = {}


# Loop through all files in the folder
for filepath in glob.glob(os.path.join(folder_path, '*')):
    if os.path.isfile(filepath):  # Ensure it's a file and not a directory
        filename_l = os.path.splitext(os.path.basename(filepath))
        filename= filename_l[0]
        if filename_l[1] == '.npy':
            module = filename.split("_")[0]
            rsc_type = filename.split("_")[-1]
            info = np.load(filepath)
            try:
                sub_dict = tmp_dict[module]
                sub_dict[rsc_type] = info
            except KeyError:
                tmp_dict[module] = {rsc_type:info}

for module, sub in tmp_dict.items():
    sub['index'] = module
    file_contents.append(sub)

# Create a DataFrame from the list
df = pd.DataFrame(file_contents)
df.set_index('index', inplace=True)

pd.set_option('display.max_colwidth', None)
for rsc in TYPES:
    with open(f'{rsc}_coefs_view.txt', 'w') as file:
        file.write(df[rsc].to_string())
