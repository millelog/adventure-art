#!/usr/bin/env python3
"""
app.py

Main server application that:
- Serves the live display frontend.
- Receives audio chunks via the /upload_audio endpoint.
- Processes audio: transcription → scene composition → image generation.
- Pushes the newly generated image to connected clients using SocketIO.
- Manages character data through a RESTful API.
"""

import os
from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO
import traceback

# Import downstream processing modules.
from adventure_art.server import transcribe
from adventure_art.server import scene_composer
from adventure_art.server import image_generator
from adventure_art.server import character_store

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Update this for production.
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")

@socketio.on('new_image')
def handle_new_image(data):
    """Handle new image event and broadcast it to all clients."""
    print("Received new image:", data)
    # Broadcast the image URL to all clients (including sender)
    socketio.emit('image_update', data)

@app.route('/')
def index():
    """Render the main display page."""
    return render_template('index.html')

# Character Management Routes
@app.route('/characters', methods=['GET'])
def get_characters():
    """Get all characters."""
    try:
        characters = character_store.get_all_characters()
        return jsonify(characters)
    except Exception as e:
        print("Error getting characters:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/characters/<character_id>', methods=['GET'])
def get_character(character_id):
    """Get a specific character by ID."""
    try:
        character = character_store.get_character(character_id)
        if character is None:
            return jsonify({"error": "Character not found"}), 404
        return jsonify(character)
    except Exception as e:
        print("Error getting character:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/characters/<character_id>', methods=['POST'])
def save_character(character_id):
    """Add or update a character."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        character_data = {
            "name": data.get("name"),
            "description": data.get("description")
        }
        
        character_store.add_or_update_character(character_id, character_data)
        return jsonify({"message": "Character saved successfully"})
    except Exception as e:
        print("Error saving character:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/characters/<character_id>', methods=['DELETE'])
def delete_character(character_id):
    """Delete a character."""
    try:
        if character_store.remove_character(character_id):
            return jsonify({"message": "Character deleted successfully"})
        return jsonify({"error": "Character not found"}), 404
    except Exception as e:
        print("Error deleting character:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Endpoint for receiving audio chunks from the client recorder."""
    if 'audio' not in request.files:
        return "Missing audio file", 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return "No file selected", 400

    try:
        # Step 1: Transcribe the audio using Whisper (or your transcription module).
        transcript = transcribe.transcribe_audio(audio_file)
        print("Transcript:", transcript)

        # Step 2: Compose a detailed scene description using the transcript and character data.
        scene_description = scene_composer.compose_scene(transcript)
        print("Scene Description:", scene_description)

        # Step 3: Generate an image for the scene using DALL-E 3.
        image_url = image_generator.generate_image(scene_description)
        print("Generated Image URL:", image_url)

        # Step 4: Emit the new image URL to all connected clients.
        socketio.emit('new_image', {'image_url': image_url})
        return "Audio processed successfully", 200

    except Exception as e:
        print("Error processing audio chunk:", e)
        traceback.print_exc()
        return "Internal Server Error", 500


if __name__ == '__main__':
    # Run the Flask-SocketIO app.
    # In production, remove debug=True and configure host/port as needed.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
