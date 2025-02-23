"""
character_store.py

Module to manage character data storage, including character descriptions.
"""

import os
import json
from pathlib import Path

# Get the base directory for character data storage
CHARACTER_DATA_DIR = os.getenv('CHARACTER_DATA_PATH', 'character_data')

# Ensure the character data directory exists
os.makedirs(CHARACTER_DATA_DIR, exist_ok=True)

def get_character_file_path():
    """Get the path to the character data JSON file."""
    return os.path.join(CHARACTER_DATA_DIR, 'characters.json')

def load_characters():
    """Load all character data from the JSON file."""
    file_path = get_character_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_characters(characters):
    """Save character data to the JSON file."""
    with open(get_character_file_path(), 'w') as f:
        json.dump(characters, f, indent=2)

def add_or_update_character(character_id, data):
    """
    Adds a new character or updates an existing character's data.
    
    Parameters:
        character_id (str): The unique identifier (or name) of the character.
        data (dict): A dictionary with character details (name and description).
    
    Returns:
        The updated dictionary of all characters.
    """
    characters = load_characters()
    characters[character_id] = data
    save_characters(characters)
    return characters

def remove_character(character_id):
    """
    Removes a character.
    
    Parameters:
        character_id (str): The unique identifier of the character to remove.
    
    Returns:
        bool: True if character was found and removed, False otherwise.
    """
    characters = load_characters()
    if character_id in characters:
        del characters[character_id]
        save_characters(characters)
        return True
    return False

def get_character(character_id):
    """Get a single character's data."""
    characters = load_characters()
    return characters.get(character_id)

def get_all_characters():
    """Get all characters' data."""
    return load_characters()

# Example usage:
if __name__ == "__main__":
    # Add or update a character
    char_id = "wizard_001"
    char_data = {
        "name": "Gandalf",
        "description": "A wise old wizard with a long white beard."
    }
    add_or_update_character(char_id, char_data)
