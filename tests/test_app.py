"""
test_app.py

Integration tests for the main Flask application.
"""

import json
from unittest.mock import patch

def test_index_route(client):
    """Test the main index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'D&D Live Scene' in response.data

@patch('server.transcribe.transcribe_audio')
@patch('server.scene_composer.compose_scene')
@patch('server.image_generator.generate_image')
def test_upload_audio_success(mock_generate_image, mock_compose_scene, mock_transcribe, client, sample_audio):
    """Test successful audio upload and processing."""
    # Mock the return values
    mock_transcribe.return_value = "The party enters a dark cave"
    mock_compose_scene.return_value = "A detailed description of the cave scene"
    mock_generate_image.return_value = "http://example.com/image.jpg"
    
    # Send the test audio file
    response = client.post(
        '/upload_audio',
        data={'audio': (sample_audio, 'test.wav')},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    assert response.data == b"Audio processed successfully"
    
    # Verify our mocks were called with expected data
    mock_transcribe.assert_called_once()
    mock_compose_scene.assert_called_once_with("The party enters a dark cave")
    mock_generate_image.assert_called_once_with("A detailed description of the cave scene")

def test_upload_audio_no_file(client):
    """Test audio upload endpoint with missing file."""
    response = client.post('/upload_audio')
    assert response.status_code == 400
    assert b"Missing audio file" in response.data

def test_socket_connection(socket_client):
    """Test Socket.IO connection and events."""
    assert socket_client.is_connected()
    
    # Test receiving a new image event
    socket_client.get_received()  # Clear any existing events
    
    test_data = {'image_url': 'http://example.com/test.jpg'}
    socket_client.emit('new_image', test_data)
    
    received = socket_client.get_received()
    assert len(received) > 0
    
    # Verify the response event
    assert received[0]['name'] == 'image_update'
    assert received[0]['args'][0] == test_data 