"""
environment_store.py

Module to manage environment data storage, including environment descriptions
and a lock flag to prevent automatic updates.
"""

import os
import json
from pathlib import Path
from adventure_art.server.config import ENVIRONMENT_DATA_PATH

# Get the base directory for environment data storage
CHARACTER_DATA_DIR = ENVIRONMENT_DATA_PATH

# Ensure the environment data directory exists
os.makedirs(CHARACTER_DATA_DIR, exist_ok=True)

def get_environment_file_path():
    """Get the path to the environment data JSON file."""
    return os.path.join(CHARACTER_DATA_DIR, 'environment.json')

def load_environment():
    """Load environment data from the JSON file."""
    file_path = get_environment_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    # Default environment with empty description and unlocked
    return {
        "description": "A generic fantasy setting with no specific details yet.",
        "locked": False
    }

def save_environment(environment_data):
    """Save environment data to the JSON file."""
    with open(get_environment_file_path(), 'w') as f:
        json.dump(environment_data, f, indent=2)

def update_environment(description, locked=None):
    """
    Updates the environment description and optionally the lock status.
    
    Parameters:
        description (str): The new environment description.
        locked (bool, optional): If provided, updates the lock status.
    
    Returns:
        The updated environment data dictionary.
    """
    environment = load_environment()
    
    # Update description if provided and not locked
    if description and (not environment.get('locked', False) or locked is not None):
        environment['description'] = description
    
    # Update lock status if provided
    if locked is not None:
        environment['locked'] = locked
    
    save_environment(environment)
    return environment

def get_environment():
    """Get the current environment data."""
    return load_environment()

def is_environment_locked():
    """Check if the environment is locked against automatic updates."""
    environment = load_environment()
    return environment.get('locked', False)

# Example usage:
if __name__ == "__main__":
    # Update environment description
    env_data = update_environment("A dark forest with tall trees blocking most of the sunlight.")
    print("Updated environment:", env_data) 