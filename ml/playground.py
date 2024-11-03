import os
import pandas as pd

import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.storage_manager import StorageManager

def get_most_recent_folder(path):
    """
    Retrieves the most recently modified folder within the given path.

    Args:
        path (str): The directory path to search.

    Returns:
        str: The path to the most recent folder.
    """
    folders = [os.path.join(path, d) for d in os.listdir(path) 
               if os.path.isdir(os.path.join(path, d))]
    if not folders:
        raise FileNotFoundError("No folders found in the base storage path.")
    most_recent_folder = max(folders, key=os.path.getmtime)
    return most_recent_folder

def load_most_recent_parquet(storage_path):
    """
    Loads the most recent Parquet file from the specified storage path.

    Args:
        storage_path (str): The directory path to search for Parquet files.

    Returns:
        pandas.DataFrame: The loaded DataFrame from the Parquet file.
    """
    parquet_files = [os.path.join(storage_path, f) 
                    for f in os.listdir(storage_path) 
                    if f.endswith('.parquet')]
    
    if not parquet_files:
        raise FileNotFoundError("No Parquet files found in the most recent folder.")
    
    most_recent_parquet = max(parquet_files, key=os.path.getmtime)
    df = pd.read_parquet(most_recent_parquet)
    return df

if __name__ == "__main__":
    storage_manager = StorageManager()
    
    # Retrieve the base storage path from StorageManager
    base_storage_path = storage_manager.get_processed_path()  # Use the new method
    
    print(f"Base Storage Path: {base_storage_path}")  # Debug statement
    
    # Dynamically get the most recent folder within the base storage path
    try:
        storage_path = get_most_recent_folder(base_storage_path)
        print(f"Most Recent Folder: {storage_path}")  # Debug statement
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    
    #todo- Specify the timeframe you want to navigate to
    timeframe = '15m'
    timeframe_path = os.path.join(storage_path, timeframe)

        # Check if the timeframe folder exists
    if not os.path.exists(timeframe_path):
        print(f"Timeframe folder not found: {timeframe_path}")
        sys.exit(1)

    print(f'Navigating into Timeframe folder: {timeframe_path}')

    # List files in the most recent folder for debugging
    print(f"Files in {timeframe_path}:")
    for file in os.listdir(timeframe_path):
        print(f" - {file}")
    
    # Load the most recent Parquet file
    try:
        df = load_most_recent_parquet(storage_path)
        print(df.info())
    except FileNotFoundError as e:
        print(e)