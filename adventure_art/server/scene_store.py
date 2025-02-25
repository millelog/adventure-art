"""
scene_store.py

Module to manage scene data storage, including the most recent scene prompt.
This helps maintain consistency between consecutive scene generations.
"""

import os
import json
from pathlib import Path
from adventure_art.server.config import CHARACTER_DATA_PATH

# Get the base directory for scene data storage (using the same base as character data)
SCENE_DATA_DIR = CHARACTER_DATA_PATH

# Ensure the scene data directory exists
os.makedirs(SCENE_DATA_DIR, exist_ok=True)

def get_scene_file_path():
    """Get the path to the scene data JSON file."""
    return os.path.join(SCENE_DATA_DIR, 'scene_data.json')

def load_scene_data():
    """Load scene data from the JSON file."""
    file_path = get_scene_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    # Default scene data with empty prompt
    return {
        "last_prompt": "",
        "timestamp": 0
    }

def save_scene_data(scene_data):
    """Save scene data to the JSON file."""
    with open(get_scene_file_path(), 'w') as f:
        json.dump(scene_data, f, indent=2)

def update_last_prompt(prompt, timestamp=None):
    """
    Updates the last scene prompt.
    
    Parameters:
        prompt (str): The scene prompt used for generation.
        timestamp (int, optional): Timestamp of when the scene was generated.
    
    Returns:
        The updated scene data dictionary.
    """
    import time
    scene_data = load_scene_data()
    
    # Update prompt
    scene_data['last_prompt'] = prompt
    
    # Update timestamp if provided, otherwise use current time
    scene_data['timestamp'] = timestamp or int(time.time())
    
    save_scene_data(scene_data)
    return scene_data

def get_last_prompt():
    """Get the most recent scene prompt."""
    scene_data = load_scene_data()
    return scene_data.get('last_prompt', "")

# Example usage:
if __name__ == "__main__":
    # Update last prompt
    scene_data = update_last_prompt("A dark forest with tall trees blocking most of the sunlight.")
    print("Updated scene data:", scene_data) 