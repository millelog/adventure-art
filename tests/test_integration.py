"""
test_integration.py

Integration tests for testing the complete audio-to-image pipeline and character management.
"""

import pytest
import json
import os
from unittest.mock import patch
import soundfile as sf
import numpy as np
from adventure_art.server.character_store import add_or_update_character, get_character, remove_character
import io

@pytest.fixture
def complex_audio():
    """Create a more complex audio sample with actual sound data."""
    duration = 2.0  # seconds
    sample_rate = 44100
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Generate a 440 Hz sine wave
    audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    # Create an in-memory WAV file
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    buffer.seek(0)
    return buffer

@pytest.fixture
def sample_characters(app):
    """Set up some sample characters for testing."""
    characters = {
        "wizard": {
            "name": "Gandalf",
            "description": "A wise old wizard with a long white beard and gray robes.",
            "traits": ["wise", "powerful", "ancient"],
            "image_path": "characters/wizard.jpg"
        },
        "warrior": {
            "name": "Aragorn",
            "description": "A noble warrior with weathered features and determined eyes.",
            "traits": ["brave", "strong", "leader"],
            "image_path": "characters/warrior.jpg"
        }
    }
    
    # Add characters to the store
    for char_id, char_data in characters.items():
        add_or_update_character(char_id, char_data)
    
    yield characters
    
    # Cleanup: remove test characters
    for char_id in characters.keys():
        remove_character(char_id)

def test_full_pipeline_with_characters(client, complex_audio, sample_characters):
    """Test the complete pipeline from audio upload to image generation with character context."""
    # Set up character store with test data
    with patch('server.character_store.get_all_characters') as mock_chars:
        mock_chars.return_value = sample_characters
        
        with patch('server.transcribe.transcribe_audio') as mock_transcribe, \
             patch('server.image_generator.generate_image') as mock_generate:
            
            # Set up mock returns
            mock_transcribe.return_value = "Gandalf raises his staff, illuminating the dark cavern while Aragorn draws his sword."
            mock_generate.return_value = "http://example.com/generated_scene.jpg"
            
            # Send audio file
            response = client.post(
                '/upload_audio',
                data={'audio': (complex_audio, 'test.wav')},
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 200
            
            # Verify the scene composition included character details
            mock_transcribe.assert_called_once()
            scene_desc_calls = mock_generate.call_args_list
            assert len(scene_desc_calls) == 1
            scene_description = scene_desc_calls[0][0][0]
            
            # Check that character details were incorporated
            for char_name in sample_characters.keys():
                assert char_name in scene_description.lower(), f"Character {char_name} not found in scene description"
            
            # Check for specific character actions from the transcript
            assert "staff" in scene_description.lower()
            assert "sword" in scene_description.lower()

def test_character_store_persistence(app, sample_characters):
    """Test that character data persists correctly and can be retrieved."""
    # Try to retrieve each character
    for char_id, expected_data in sample_characters.items():
        stored_data = get_character(char_id)
        assert stored_data is not None
        assert stored_data['name'] == expected_data['name']
        assert stored_data['description'] == expected_data['description']
        assert stored_data['traits'] == expected_data['traits']

def test_scene_composition_with_missing_characters(client, complex_audio):
    """Test scene composition behavior when referenced characters don't exist."""
    with patch('server.transcribe.transcribe_audio') as mock_transcribe, \
         patch('server.image_generator.generate_image') as mock_generate:
        
        mock_transcribe.return_value = "The mysterious wizard casts a powerful spell."
        mock_generate.return_value = "http://example.com/generic_scene.jpg"
        
        response = client.post(
            '/upload_audio',
            data={'audio': (complex_audio, 'test.wav')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        scene_desc_calls = mock_generate.call_args_list
        scene_description = scene_desc_calls[0][0][0]
        
        # Scene should still be generated even without character details
        assert "wizard" in scene_description.lower()
        assert "spell" in scene_description.lower()

def test_socket_image_broadcast(socket_client, client, complex_audio, sample_characters):
    """Test that new images are properly broadcast to all connected clients."""
    with patch('server.transcribe.transcribe_audio') as mock_transcribe, \
         patch('server.image_generator.generate_image') as mock_generate:
        
        mock_transcribe.return_value = "Gandalf and Aragorn stand ready for battle."
        mock_generate.return_value = "http://example.com/battle_scene.jpg"
        
        # Clear any existing events
        socket_client.get_received()
        
        # Trigger image generation through audio upload
        response = client.post(
            '/upload_audio',
            data={'audio': (complex_audio, 'test.wav')},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        
        # Check that the socket client received the new image event
        received = socket_client.get_received()
        assert len(received) > 0
        assert received[0]['name'] == 'new_image'
        assert received[0]['args'][0]['image_url'] == "http://example.com/battle_scene.jpg"

def test_error_handling(client, complex_audio):
    """Test error handling in the pipeline."""
    # Test transcription error
    with patch('server.transcribe.transcribe_audio', side_effect=Exception("Transcription failed")):
        # Create a fresh copy of the audio data for each test
        audio_copy = complex_audio.getvalue()
        audio_buffer = io.BytesIO(audio_copy)
        response = client.post(
            '/upload_audio',
            data={'audio': (audio_buffer, 'test.wav')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 500
        assert b"Internal Server Error" in response.data

    # Test scene composition error
    with patch('server.transcribe.transcribe_audio') as mock_transcribe, \
         patch('server.scene_composer.compose_scene', side_effect=Exception("Scene composition failed")):
        
        mock_transcribe.return_value = "Test transcript"
        # Create a fresh copy of the audio data
        audio_copy = complex_audio.getvalue()
        audio_buffer = io.BytesIO(audio_copy)
        response = client.post(
            '/upload_audio',
            data={'audio': (audio_buffer, 'test.wav')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 500
        assert b"Internal Server Error" in response.data

    # Test image generation error
    with patch('server.transcribe.transcribe_audio') as mock_transcribe, \
         patch('server.scene_composer.compose_scene') as mock_compose, \
         patch('server.image_generator.generate_image', side_effect=Exception("Image generation failed")):
        
        mock_transcribe.return_value = "Test transcript"
        mock_compose.return_value = "Test scene description"
        # Create a fresh copy of the audio data
        audio_copy = complex_audio.getvalue()
        audio_buffer = io.BytesIO(audio_copy)
        response = client.post(
            '/upload_audio',
            data={'audio': (audio_buffer, 'test.wav')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 500
        assert b"Internal Server Error" in response.data 