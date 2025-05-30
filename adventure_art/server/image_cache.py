"""
image_cache.py

Module to manage a local cache of generated images, storing only the N most recent images.
"""

import os
import requests
from collections import deque
from pathlib import Path
import time
import shutil

# Configuration
CACHE_SIZE = 10  # Maximum number of images to store
CACHE_DIR = os.path.join(os.getenv('CHARACTER_DATA_PATH', 'character_data'), 'scene_cache')

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

# Keep track of cached images in order
cached_images = deque(maxlen=CACHE_SIZE)

def download_and_cache_image(image_source):
    """
    Copies an image from a source (URL or local path) to the cache.
    If cache is full, removes oldest image.
    
    Parameters:
        image_source (str): URL or local file path of the image
        
    Returns:
        str: Filename of the cached image that can be served
    """
    try:
        # Generate a filename based on timestamp
        timestamp = int(time.time())
        filename = f"scene_{timestamp}.png"
        filepath = os.path.join(CACHE_DIR, filename)
        
        # Check if source is a URL or local file
        is_url = image_source.startswith(('http://', 'https://'))
        
        if is_url:
            # Download from URL
            response = requests.get(image_source, stream=True)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)
        else:
            # Copy from local file
            shutil.copy2(image_source, filepath)
            # Remove the temporary file since we've copied it to our cache
            try:
                os.remove(image_source)
            except Exception as e:
                print(f"Warning: Could not remove temporary file {image_source}: {e}")
        
        # Add to cache tracking
        cached_images.append(filename)
        
        # If we've exceeded cache size, remove oldest image
        if len(os.listdir(CACHE_DIR)) > CACHE_SIZE:
            files_to_remove = sorted(Path(CACHE_DIR).glob('scene_*.png'))[:-CACHE_SIZE]
            for old_file in files_to_remove:
                try:
                    os.remove(old_file)
                except Exception as e:
                    print(f"Error removing old cached image {old_file}: {e}")
        
        return filename
        
    except Exception as e:
        print(f"Error caching image: {e}")
        return None

def get_cached_image_path(filename):
    """
    Get the full path to a cached image.
    
    Parameters:
        filename (str): Name of the cached image file
        
    Returns:
        str: Full path to the cached image
    """
    return os.path.join(CACHE_DIR, filename)

def clear_cache():
    """Clear all cached images."""
    try:
        for file in Path(CACHE_DIR).glob('scene_*.png'):
            os.remove(file)
        cached_images.clear()
    except Exception as e:
        print(f"Error clearing cache: {e}") 