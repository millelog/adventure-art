"""
character_store.py

A simple file-based character store that maintains character descriptions and reference image paths.
Data is stored in a JSON file located in the directory specified by config.CHARACTER_DATA_PATH.
"""

import os
import json
from config import CHARACTER_DATA_PATH

# Define the filename for storing character data
CHARACTER_FILE = os.path.join(CHARACTER_DATA_PATH, 'characters.json')

def ensure_data_directory():
    """Ensure that the CHARACTER_DATA_PATH directory exists."""
    if not os.path.exists(CHARACTER_DATA_PATH):
        os.makedirs(CHARACTER_DATA_PATH)

def load_characters():
    """
    Loads character data from the JSON file.
    
    Returns:
        A dictionary where keys are character IDs/names and values are their details.
        Returns an empty dict if the file doesn't exist.
    """
    ensure_data_directory()
    if not os.path.isfile(CHARACTER_FILE):
        return {}
    try:
        with open(CHARACTER_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading characters: {e}")
        return {}

def save_characters(characters):
    """
    Saves the character data dictionary to the JSON file.
    
    Parameters:
        characters (dict): The dictionary containing character data.
    """
    ensure_data_directory()
    try:
        with open(CHARACTER_FILE, 'w', encoding='utf-8') as f:
            json.dump(characters, f, indent=4)
    except Exception as e:
        print(f"Error saving characters: {e}")

def get_all_characters():
    """
    Retrieves all characters.
    
    Returns:
        A dictionary of all characters.
    """
    return load_characters()

def get_character(character_id):
    """
    Retrieves details for a single character.
    
    Parameters:
        character_id (str): The unique identifier (or name) of the character.
    
    Returns:
        A dictionary containing the character's details, or None if not found.
    """
    characters = load_characters()
    return characters.get(character_id)

def add_or_update_character(character_id, data):
    """
    Adds a new character or updates an existing character's data.
    
    Parameters:
        character_id (str): The unique identifier (or name) of the character.
        data (dict): A dictionary with character details, such as:
            - description: A textual description of the character.
            - image_path: Path to the reference image.
            - any other metadata.
    
    Returns:
        The updated dictionary of all characters.
    """
    characters = load_characters()
    characters[character_id] = data
    save_characters(characters)
    return characters

def remove_character(character_id):
    """
    Removes a character from the store.
    
    Parameters:
        character_id (str): The unique identifier (or name) of the character to remove.
    
    Returns:
        True if the character was removed, False otherwise.
    """
    characters = load_characters()
    if character_id in characters:
        del characters[character_id]
        save_characters(characters)
        return True
    return False

# Example usage:
if __name__ == "__main__":
    # Add or update a character
    char_id = "wizard_001"
    char_data = {
        "description": "A wise old wizard with a long white beard.",
        "image_path": "path/to/wizard_reference.jpg"
    }
    add_or_update_character(char_id, char_data)

    # Retrieve and print all characters
    all_chars = get_all_characters()
    print("All Characters:")
    print(json.dumps(all_chars, indent=4))
