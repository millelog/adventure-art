"""
conftest.py

Contains pytest fixtures that can be shared across multiple test files.
"""

import pytest
from adventure_art.server.app import app as flask_app
import os
import tempfile
import json

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temp file to store test character data
    with tempfile.TemporaryDirectory() as temp_dir:
        # Update the character data path for testing
        flask_app.config.update({
            'TESTING': True,
            'CHARACTER_DATA_PATH': temp_dir,
            'SECRET_KEY': 'test_secret_key'
        })
        
        yield flask_app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def socket_client(app):
    """A test client for Socket.IO."""
    from flask_socketio import SocketIOTestClient
    from adventure_art.server.app import socketio
    return SocketIOTestClient(app, socketio)

@pytest.fixture
def sample_audio():
    """Create a sample audio file for testing."""
    import numpy as np
    import soundfile as sf
    import io
    
    # Generate 1 second of silence as test audio
    sample_rate = 44100
    audio_data = np.zeros(sample_rate)
    
    # Create an in-memory WAV file
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    buffer.seek(0)
    
    return buffer

@pytest.fixture
def sample_characters():
    """Sample character data for testing."""
    return {
        "wizard_001": {
            "name": "Gandalf",
            "description": "A wise old wizard with a long white beard.",
            "image_path": "path/to/wizard_reference.jpg"
        },
        "warrior_001": {
            "name": "Aragorn",
            "description": "A noble warrior with weathered features.",
            "image_path": "path/to/warrior_reference.jpg"
        }
    } 