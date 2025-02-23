"""
test_character_store.py

Tests for the character store functionality.
"""

import os
import json
from adventure_art.server import character_store

def test_add_and_retrieve_character(app):
    """Test adding and retrieving a character."""
    char_id = "test_wizard"
    char_data = {
        "name": "Test Wizard",
        "description": "A test wizard character",
        "image_path": "test/path/wizard.jpg"
    }
    
    # Add the character
    character_store.add_or_update_character(char_id, char_data)
    
    # Retrieve the character
    retrieved = character_store.get_character(char_id)
    assert retrieved == char_data
    
    # Check all characters
    all_chars = character_store.get_all_characters()
    assert char_id in all_chars
    assert all_chars[char_id] == char_data

def test_remove_character(app):
    """Test removing a character."""
    char_id = "test_warrior"
    char_data = {
        "name": "Test Warrior",
        "description": "A test warrior character"
    }
    
    # Add and then remove the character
    character_store.add_or_update_character(char_id, char_data)
    assert character_store.remove_character(char_id)
    
    # Verify character was removed
    assert character_store.get_character(char_id) is None

def test_update_existing_character(app):
    """Test updating an existing character."""
    char_id = "test_rogue"
    original_data = {
        "name": "Test Rogue",
        "description": "Original description"
    }
    updated_data = {
        "name": "Test Rogue",
        "description": "Updated description"
    }
    
    # Add original character
    character_store.add_or_update_character(char_id, original_data)
    
    # Update character
    character_store.add_or_update_character(char_id, updated_data)
    
    # Verify update
    retrieved = character_store.get_character(char_id)
    assert retrieved == updated_data 