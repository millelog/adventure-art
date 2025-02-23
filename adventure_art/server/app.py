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
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
dotenv_path = Path(__file__).resolve().parent.parent.parent / '.env'
success = load_dotenv(dotenv_path)


from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
import traceback

# Import downstream processing modules.
from adventure_art.server import transcribe
from adventure_art.server import scene_composer
from adventure_art.server import image_generator
from adventure_art.server import character_store
from adventure_art.server import image_cache

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')  # Get from .env
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print("Client connected")
    # Send the latest cached image if available
    latest_image = get_latest_cached_image()
    if latest_image:
        socketio.emit('new_image', {'image_url': f'/scene_images/{latest_image}'})

def get_latest_cached_image():
    """Get the filename of the most recent cached image."""
    try:
        files = sorted(Path(image_cache.CACHE_DIR).glob('scene_*.png'))
        if files:
            return files[-1].name
    except Exception as e:
        print(f"Error getting latest cached image: {e}")
    return None

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
        
        if not character_data["name"] or not character_data["description"]:
            return jsonify({"error": "Name and description are required"}), 400
        
        updated_characters = character_store.add_or_update_character(character_id, character_data)
        return jsonify(updated_characters)
            
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
        # Step 1: Transcribe the audio using Whisper
        try:
            transcript = transcribe.transcribe_audio(audio_file)
            print("Transcript:", transcript)
        except Exception as e:
            print(f"Error during transcription: {e}")
            return "Transcription failed", 500

        # Step 2: Compose a scene description
        scene_description = scene_composer.compose_scene(transcript)
        if scene_description:
            print("Scene Description:", scene_description)
        else:
            print("No valid scene could be composed")
            return "No valid scene could be composed", 200

        # Step 3: Generate an image for the scene
        dalle_url = image_generator.generate_image(scene_description)
        if dalle_url:
            print("Generated Image URL:", dalle_url)
            
            # Step 4: Cache the image locally
            cached_filename = image_cache.download_and_cache_image(dalle_url)
            if cached_filename:
                # Step 5: Emit the cached image URL to all connected clients
                cached_url = f'/scene_images/{cached_filename}'
                print("Emitting new image URL:", cached_url)
                socketio.emit('new_image', {'image_url': cached_url})
                return "Audio processed successfully", 200
            else:
                print("Failed to cache the image")
                return "Image caching failed", 500
        else:
            print("Image generation failed")
            return "Image generation failed", 200

    except Exception as e:
        print("Error processing audio chunk:", e)
        traceback.print_exc()
        return "Internal Server Error", 500

# Add route to serve character images
@app.route('/character_images/<path:filename>')
def serve_character_image(filename):
    """Serve character images from the images directory."""
    try:
        return send_from_directory(character_store.IMAGES_DIR, filename)
    except Exception as e:
        print(f"Error serving character image {filename}: {e}")
        return "Image not found", 404

# Add route to serve cached scene images
@app.route('/scene_images/<path:filename>')
def serve_scene_image(filename):
    """Serve scene images from the cache directory."""
    try:
        return send_from_directory(image_cache.CACHE_DIR, filename)
    except Exception as e:
        print(f"Error serving scene image {filename}: {e}")
        return "Image not found", 404

if __name__ == '__main__':
    # Run the Flask-SocketIO app.
    # In production, remove debug=True and configure host/port as needed.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
