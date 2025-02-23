"""
test_components.py

Unit tests for individual components of the system.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import os
import numpy as np
import soundfile as sf
from adventure_art.server import transcribe, scene_composer, image_generator

@pytest.fixture
def whisper_audio():
    """Create a simple audio file for testing Whisper transcription."""
    duration = 1.0
    sample_rate = 16000  # Whisper expects 16kHz
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    import io
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    buffer.seek(0)
    return buffer

def test_transcribe_audio(whisper_audio):
    """Test audio transcription with the Whisper model."""
    with patch('whisper.load_model') as mock_load_model:
        # Mock the Whisper model and its transcribe method
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "Test transcription"}
        mock_load_model.return_value = mock_model
        
        # Test transcription
        result = transcribe.transcribe_audio(whisper_audio)
        assert result == "Test transcription"
        mock_model.transcribe.assert_called_once()

def test_image_generation():
    """Test image generation with various scene descriptions."""
    test_descriptions = [
        "A majestic dragon soaring over mountains",
        "A cozy tavern filled with adventurers"
    ]
    
    with patch('openai.Image.create') as mock_image_create:
        for description in test_descriptions:
            mock_image_create.return_value = {
                'data': [{'url': f"http://example.com/image_{hash(description)}.jpg"}]
            }
            
            result = image_generator.generate_image(description)
            assert result.startswith("http://example.com/image_")
            assert result.endswith(".jpg")
            mock_image_create.assert_called_with(
                prompt=description,
                n=1,
                size="1024x1024"
            )

def test_character_store_operations(tmp_path):
    """Test character store operations in isolation."""
    from adventure_art.server.character_store import (
        add_or_update_character,
        get_character,
        get_all_characters,
        remove_character
    )
    import adventure_art.server.character_store
    import adventure_art.server.config
    import shutil
    
    # Create a fresh temporary directory for the test
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
    os.makedirs(tmp_path)
    
    # Store original paths
    original_data_path = adventure_art.server.config.CHARACTER_DATA_PATH
    original_char_file = adventure_art.server.character_store.CHARACTER_FILE
    
    try:
        # Set up test-specific paths
        test_data_path = str(tmp_path)
        test_char_file = os.path.join(test_data_path, 'test_characters.json')
        
        # Override the paths for testing
        adventure_art.server.config.CHARACTER_DATA_PATH = test_data_path
        adventure_art.server.character_store.CHARACTER_FILE = test_char_file
        
        # Test character addition
        test_char = {
            "name": "Test Character",
            "description": "A test character",
            "traits": ["test"]
        }
        
        add_or_update_character("test_char", test_char)
        retrieved = get_character("test_char")
        assert retrieved == test_char
        
        # Test character update
        updated_char = test_char.copy()
        updated_char["description"] = "Updated description"
        add_or_update_character("test_char", updated_char)
        retrieved = get_character("test_char")
        assert retrieved["description"] == "Updated description"
        
        # Test getting all characters
        all_chars = get_all_characters()
        assert len(all_chars) == 1
        assert "test_char" in all_chars
        
        # Test character removal
        assert remove_character("test_char")
        assert get_character("test_char") is None
        
        # Test removing non-existent character
        assert not remove_character("nonexistent_char")
        
    finally:
        # Restore original paths
        adventure_art.server.config.CHARACTER_DATA_PATH = original_data_path
        adventure_art.server.character_store.CHARACTER_FILE = original_char_file
        
        # Clean up test directory
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path)

def test_config_loading():
    """Test configuration loading and environment variable handling."""
    import os
    from adventure_art.server.config import (
        CHUNK_DURATION,
        SAMPLE_RATE,
        CHANNELS,
        CHARACTER_DATA_PATH
    )
    
    # Test default values
    assert isinstance(CHUNK_DURATION, int)
    assert isinstance(SAMPLE_RATE, int)
    assert isinstance(CHANNELS, int)
    assert isinstance(CHARACTER_DATA_PATH, str)
    
    # Test environment variable override
    os.environ['CHUNK_DURATION'] = '30'
    os.environ['SAMPLE_RATE'] = '48000'
    
    # Reload config
    import importlib
    import adventure_art.server.config
    importlib.reload(adventure_art.server.config)
    
    assert adventure_art.server.config.CHUNK_DURATION == 30
    assert adventure_art.server.config.SAMPLE_RATE == 48000 