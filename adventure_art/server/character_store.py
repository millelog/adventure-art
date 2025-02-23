"""
character_store.py

Module to manage character data storage, including character descriptions and images.
"""

import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

# Get the base directory for character data storage
CHARACTER_DATA_DIR = os.getenv('CHARACTER_DATA_PATH', 'character_data')
IMAGES_DIR = os.path.join(CHARACTER_DATA_DIR, 'images')

# Ensure the character data and images directories exist
os.makedirs(CHARACTER_DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

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

def save_character_image(image_file):
    """
    Save a character image file and return its URL path.
    
    Parameters:
        image_file: FileStorage object from Flask
    
    Returns:
        str: URL path to the saved image
    """
    if not image_file:
        return None
        
    # Generate a unique filename
    filename = secure_filename(image_file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(IMAGES_DIR, unique_filename)
    
    # Save the image
    image_file.save(file_path)
    
    # Return the URL path
    return f'/character_images/{unique_filename}'

def add_or_update_character(character_id, data, image_file=None):
    """
    Adds a new character or updates an existing character's data.
    
    Parameters:
        character_id (str): The unique identifier (or name) of the character.
        data (dict): A dictionary with character details.
        image_file: Optional FileStorage object for character image.
    
    Returns:
        The updated dictionary of all characters.
    """
    characters = load_characters()
    
    # Handle image upload if provided
    if image_file:
        image_url = save_character_image(image_file)
        if image_url:
            data['image_url'] = image_url
    
    # Preserve existing image_url if no new image is provided
    if character_id in characters and 'image_url' in characters[character_id] and 'image_url' not in data:
        data['image_url'] = characters[character_id]['image_url']
    
    characters[character_id] = data
    save_characters(characters)
    return characters

def remove_character(character_id):
    """
    Removes a character and their associated image.
    
    Parameters:
        character_id (str): The unique identifier of the character to remove.
    
    Returns:
        bool: True if character was found and removed, False otherwise.
    """
    characters = load_characters()
    if character_id in characters:
        # Remove associated image file if it exists
        if 'image_url' in characters[character_id]:
            image_path = os.path.join(CHARACTER_DATA_DIR, characters[character_id]['image_url'].lstrip('/'))
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Error removing image file: {e}")
        
        # Remove character from data
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
        "description": "A wise old wizard with a long white beard.",
        "image_path": "path/to/wizard_reference.jpg"
    }
    add_or_update_character(char_id, char_data)

    # Retrieve and print all characters
    all_chars = get_all_characters()
    print("All Characters:")
    print(json.dumps(all_chars, indent=4))
