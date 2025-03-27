"""
style_store.py

Module to manage global image style preferences.
This store controls high-level style directives that are applied to all generated images.
"""

import os
import json
from pathlib import Path
from adventure_art.server.config import CHARACTER_DATA_PATH

# Get the base directory for style data storage (using the same base as character data)
STYLE_DATA_DIR = CHARACTER_DATA_PATH

# Ensure the style data directory exists
os.makedirs(STYLE_DATA_DIR, exist_ok=True)

def get_style_file_path():
    """Get the path to the style data JSON file."""
    return os.path.join(STYLE_DATA_DIR, 'style_data.json')

def load_style_data():
    """Load style data from the JSON file."""
    file_path = get_style_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    # Default style data - a comprehensive style directive for fantasy artwork
    return {
        "style_text": "Art style: fantasy oil painting. Color palette: vibrant and rich. Lighting: dramatic with strong shadows and highlights. Composition: balanced and cinematic. Level of detail: high with carefully rendered textures."
    }

def save_style_data(style_data):
    """Save style data to the JSON file."""
    with open(get_style_file_path(), 'w') as f:
        json.dump(style_data, f, indent=2)

def update_style(style_text=None):
    """
    Updates the style preferences.
    
    Parameters:
        style_text (str, optional): Full style directive text
    
    Returns:
        The updated style data dictionary.
    """
    style_data = load_style_data()
    
    # Update style text if provided
    if style_text is not None:
        style_data['style_text'] = style_text
    
    save_style_data(style_data)
    return style_data

def get_style():
    """
    Get the current style preferences.
    
    Returns:
        dict: The current style data.
    """
    return load_style_data()

def get_style_directive():
    """
    Get the current style directive text.
    
    Returns:
        str: The current style directive.
    """
    style_data = load_style_data()
    return style_data.get('style_text', '')

# Example usage:
if __name__ == "__main__":
    # Update style
    style_data = update_style(
        style_text="Art style: fantasy oil painting with intricate details. Color palette: rich and vibrant with golden accents. Lighting: dramatic side lighting creating long shadows."
    )
    print("Updated style data:", style_data)
    
    # Get style directive
    directive = get_style_directive()
    print("Style directive:", directive) 