import os
import pandas as pd
import re

def get_highest_solo_inference_path(parent_path):
    """
    Finds the subfolder with the highest number in solo_inference_<number>.
    If solo_inference exists, it's treated as solo_inference_0.
    """
    if not os.path.exists(parent_path):
        return None
    
    subfolders = [f for f in os.listdir(parent_path) if os.path.isdir(os.path.join(parent_path, f))]
    solo_folders = [f for f in subfolders if f == 'solo_inference' or f.startswith('solo_inference_')]
    
    if not solo_folders:
        return None
    
    def extract_number(folder_name):
        if folder_name == 'solo_inference':
            return 0
        match = re.search(r'solo_inference_(\d+)', folder_name)
        if match:
            return int(match.group(1))
        return -1

    highest_folder = max(solo_folders, key=extract_number)
    return os.path.join(parent_path, highest_folder)

def load_overall_results(folder_path):
    """
    Loads overall_results.csv from the highest solo_inference folder.
    """
    inference_path = get_highest_solo_inference_path(folder_path)
    if not inference_path:
        return None
    
    csv_path = os.path.join(inference_path, 'overall_results.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

def get_folder_label(folder_path):
    """
    Returns the base name of the folder path as label.
    """
    return os.path.basename(folder_path.rstrip(os.sep))
