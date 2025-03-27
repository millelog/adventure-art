#!/usr/bin/env python3
"""
app.py

Main server application that:
- Serves the live display frontend.
- Receives audio chunks via the /upload_audio endpoint.
- Processes audio: transcription → environment analysis → scene composition → image generation.
- Pushes the newly generated image to connected clients using SocketIO.
- Manages character and environment data through a RESTful API.
- Tracks session history including transcripts, prompts, and images.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from flask import make_response

# Load .env file from project root
dotenv_path = Path(__file__).resolve().parent.parent.parent / '.env'
success = load_dotenv(dotenv_path)


from flask import Flask, request, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO
import traceback

# Import downstream processing modules.
from adventure_art.server import transcribe
from adventure_art.server import environment_analyzer
from adventure_art.server import scene_composer
from adventure_art.server import image_generator
from adventure_art.server import character_store
from adventure_art.server import environment_store
from adventure_art.server import image_cache
from adventure_art.server import session_history
from adventure_art.server import scene_store
from adventure_art.server import style_store

# Create Flask app and SocketIO instance
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Temporary storage for the current transcript
current_transcript = None

# Ensure the necessary directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('character_images', exist_ok=True)
os.makedirs('scene_images', exist_ok=True)

# Initialize the session history
session_history.init()

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    
    # Send the current environment to the client
    try:
        environment = environment_store.get_environment()
        if environment:
            socketio.emit('environment_update', {'description': environment.get('description', '')})
    except Exception as e:
        print(f"Error sending environment on connect: {e}")
    
    # Send the latest cached image to the client
    try:
        latest_image = get_latest_cached_image()
        if latest_image:
            socketio.emit('new_image', {'image_url': latest_image})
    except Exception as e:
        print(f"Error sending latest image on connect: {e}")

def get_latest_cached_image():
    """Get the URL of the latest cached image."""
    try:
        # Get all PNG files in the cache directory
        cache_dir = Path(image_cache.CACHE_DIR)
        files = sorted(list(cache_dir.glob('scene_*.png')), key=lambda x: x.stat().st_mtime)
        if files:
            latest_filename = files[-1].name
            return f'/scene_images/{latest_filename}'
    except Exception as e:
        print(f"Error getting latest cached image: {e}")
    return None

@socketio.on('new_image')
def handle_new_image(data):
    """Handle new image event from client."""
    print('New image received:', data)
    # This event is for future use, currently images are pushed from the server

@app.route('/')
def index():
    """Serve the main application page."""
    sessions_url = '/sessions/view'
    return render_template('index.html', sessions_url=sessions_url)

@app.route('/characters', methods=['GET'])
def get_characters():
    """Get all characters."""
    try:
        characters = character_store.get_all_characters()
        return jsonify(characters)
    except Exception as e:
        print(f"Error getting characters: {e}")
        return "Error getting characters", 500

@app.route('/characters/<character_id>', methods=['GET'])
def get_character(character_id):
    """Get a specific character by ID."""
    try:
        character = character_store.get_character(character_id)
        if character:
            return jsonify(character)
        else:
            return "Character not found", 404
    except Exception as e:
        print(f"Error getting character: {e}")
        return "Error getting character", 500

@app.route('/characters/<character_id>', methods=['POST'])
def save_character(character_id):
    """Save or update a character."""
    try:
        data = request.json
        if not data:
            return "Missing character data", 400
        
        name = data.get('name', '')
        description = data.get('description', '')
        
        if not name or not description:
            return "Name and description are required", 400
        
        character_data = {
            "name": name,
            "description": description
        }
        
        character_store.add_or_update_character(character_id, character_data)
        return "Character saved", 200
    except Exception as e:
        print(f"Error saving character: {e}")
        traceback.print_exc()
        return "Error saving character", 500

@app.route('/characters/<character_id>', methods=['DELETE'])
def delete_character(character_id):
    """Delete a character."""
    try:
        character_store.remove_character(character_id)
        return "Character deleted", 200
    except Exception as e:
        print(f"Error deleting character: {e}")
        return "Error deleting character", 500

@app.route('/environment', methods=['GET'])
def get_environment():
    """Get the current environment description."""
    try:
        environment = environment_store.get_environment()
        return jsonify(environment)
    except Exception as e:
        print(f"Error getting environment: {e}")
        return "Error getting environment", 500

@app.route('/environment', methods=['POST'])
def save_environment():
    """Save the environment description."""
    try:
        data = request.json
        if not data:
            return "Missing environment data", 400
        
        description = data.get('description', '')
        locked = data.get('locked', False)
        
        environment_store.update_environment(description, locked)
        
        # Emit the environment update to all connected clients
        emit_environment_update(description)
        
        return "Environment saved", 200
    except Exception as e:
        print(f"Error saving environment: {e}")
        return "Error saving environment", 500

@app.route('/style', methods=['GET'])
def get_style():
    """Get the current style settings."""
    try:
        style_data = style_store.get_style()
        return jsonify(style_data)
    except Exception as e:
        print(f"Error getting style: {e}")
        return "Error getting style", 500

@app.route('/style', methods=['POST'])
def save_style():
    """Save the style settings."""
    try:
        data = request.json
        if not data:
            return "Missing style data", 400
        
        # Extract style text from request data
        style_text = data.get('style_text')
        
        if not style_text:
            return "Style text is required", 400
        
        # Update style settings
        style_store.update_style(style_text=style_text)
        
        # Get the resulting style directive for clients
        style_directive = style_store.get_style_directive()
        
        # Emit the style update to all connected clients
        socketio.emit('style_update', {
            'style_data': {'style_text': style_text},
            'style_directive': style_directive
        })
        
        return "Style saved", 200
    except Exception as e:
        print(f"Error saving style: {e}")
        traceback.print_exc()
        return "Error saving style", 500

@app.route('/style/reset', methods=['POST'])
def reset_style():
    """Reset style settings to defaults."""
    try:
        # Get default style data (which is loaded when we create a new object)
        default_style = style_store.load_style_data()
        
        # Update style settings with default
        style_store.update_style(style_text=default_style['style_text'])
        
        # Get the resulting style directive
        style_directive = style_store.get_style_directive()
        
        # Emit the style update to all connected clients
        socketio.emit('style_update', {
            'style_data': default_style,
            'style_directive': style_directive
        })
        
        return jsonify({
            "message": "Style reset to defaults",
            "style_data": default_style,
            "style_directive": style_directive
        })
    except Exception as e:
        print(f"Error resetting style: {e}")
        return "Error resetting style", 500

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    """Endpoint for receiving audio chunks from the client recorder."""
    global current_transcript
    
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
            
            # Store the transcript for later use in session history
            current_transcript = transcript
        except Exception as e:
            print(f"Error during transcription: {e}")
            return "Transcription failed", 500

        # Step 2: Analyze the transcript and update environment if needed
        try:
            environment_analyzer.analyze_transcript(transcript)
        except Exception as e:
            print(f"Error during environment analysis: {e}")
            # Continue processing even if environment analysis fails

        # Step 3: Compose a scene description
        scene_description = scene_composer.compose_scene(transcript)
        if scene_description:
            print("Scene Description:", scene_description)
            
            # Emit the scene prompt to all connected clients
            socketio.emit('scene_prompt_update', {'prompt': scene_description})
        else:
            print("No valid scene could be composed")
            return "No valid scene could be composed", 200

        # Step 4: Generate an image for the scene
        dalle_url = image_generator.generate_image(scene_description)
        if dalle_url:
            print("Generated Image URL:", dalle_url)
            
            # Step 5: Cache the image locally
            cached_filename = image_cache.download_and_cache_image(dalle_url)
            if cached_filename:
                # Step 6: Emit the cached image URL to all connected clients
                cached_url = f'/scene_images/{cached_filename}'
                print("Emitting new image URL:", cached_url)
                socketio.emit('new_image', {'image_url': cached_url})
                
                # Add combined event to session history
                try:
                    cached_path = image_cache.get_cached_image_path(cached_filename)
                    session_history.add_scene_event(current_transcript, scene_description, cached_path)
                except Exception as e:
                    print(f"Warning: Could not add scene to session history: {e}")
                
                return "Audio processed successfully", 200
            else:
                return "Failed to cache image", 500
        else:
            return "Failed to generate image", 500
    except Exception as e:
        print(f"Error processing audio: {e}")
        traceback.print_exc()
        return "Error processing audio", 500

@app.route('/scene_prompt', methods=['GET'])
def get_scene_prompt():
    """Get the current scene prompt."""
    try:
        prompt = scene_store.get_last_prompt()
        return jsonify({"prompt": prompt})
    except Exception as e:
        print(f"Error getting scene prompt: {e}")
        return "Error getting scene prompt", 500

@app.route('/scene_prompt', methods=['DELETE'])
def clear_scene_prompt():
    """Clear the current scene prompt."""
    try:
        scene_store.update_last_prompt("")
        return "Scene prompt cleared", 200
    except Exception as e:
        print(f"Error clearing scene prompt: {e}")
        return "Error clearing scene prompt", 500

@app.route('/character_images/<path:filename>')
def serve_character_image(filename):
    """Serve character images."""
    try:
        return send_from_directory('character_images', filename)
    except Exception as e:
        print(f"Error serving character image: {e}")
        return "Image not found", 404

@app.route('/scene_images/<path:filename>')
def serve_scene_image(filename):
    """Serve scene images."""
    try:
        return send_from_directory(image_cache.CACHE_DIR, filename)
    except Exception as e:
        print(f"Error serving scene image: {e}")
        return "Image not found", 404

def emit_environment_update(description):
    """Emit an environment update to all connected clients."""
    try:
        socketio.emit('environment_update', {'description': description})
    except Exception as e:
        print(f"Error emitting environment update: {e}")

# Add new routes for session history
@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Get a list of all sessions."""
    sessions = session_history.get_all_sessions()
    return jsonify(sessions)

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get a specific session by ID."""
    session = session_history.get_session_by_id(session_id)
    if session:
        return jsonify(session)
    else:
        return "Session not found", 404

@app.route('/sessions/current', methods=['GET'])
def get_current_session():
    """Get the current session."""
    session_id = session_history.get_current_session_id()
    session = session_history.get_session_by_id(session_id)
    return jsonify(session)

@app.route('/session_history/images/<path:filename>')
def serve_session_image(filename):
    """Serve images from the session history directory."""
    try:
        # Handle both direct filenames and paths with session IDs
        path_parts = filename.split('/')
        if len(path_parts) >= 2:
            session_id = path_parts[0]
            image_name = path_parts[1]
            return send_from_directory(str(session_history.HISTORY_IMAGES_DIR / session_id), image_name)
        else:
            # If it's just a filename, try to serve it directly
            return send_from_directory(str(session_history.HISTORY_IMAGES_DIR), filename)
    except Exception as e:
        print(f"Error serving session image: {e}")
        return "Image not found", 404

@app.route('/sessions/view')
def view_sessions():
    """Render the sessions history view page."""
    return render_template('sessions.html')

@app.route('/sessions/<session_id>/download/transcripts')
def download_transcripts(session_id):
    """Download all transcripts from a session as a text file."""
    try:
        session = session_history.get_session_by_id(session_id)
        if not session:
            return "Session not found", 404
        
        # Extract all transcripts from scene events
        transcripts = []
        for event in session['events']:
            if event['type'] == 'scene' and 'transcript' in event:
                timestamp = datetime.fromisoformat(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                transcripts.append(f"[{timestamp}]\n{event['transcript']}\n\n")
        
        # Join all transcripts into a single text file
        all_transcripts = "".join(transcripts)
        
        # Create a response with the text file
        response = make_response(all_transcripts)
        response.headers["Content-Disposition"] = f"attachment; filename=transcripts_{session_id}.txt"
        response.headers["Content-Type"] = "text/plain"
        return response
    except Exception as e:
        print(f"Error downloading transcripts: {e}")
        return "Error generating transcript file", 500

@app.route('/sessions/<session_id>/download/scene_descriptions')
def download_scene_descriptions(session_id):
    """Download all scene descriptions from a session as a text file."""
    try:
        session = session_history.get_session_by_id(session_id)
        if not session:
            return "Session not found", 404
        
        # Extract all scene descriptions from scene events
        descriptions = []
        for event in session['events']:
            if event['type'] == 'scene' and 'prompt' in event:
                timestamp = datetime.fromisoformat(event['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                descriptions.append(f"[{timestamp}]\n{event['prompt']}\n\n")
        
        # Join all descriptions into a single text file
        all_descriptions = "".join(descriptions)
        
        # Create a response with the text file
        response = make_response(all_descriptions)
        response.headers["Content-Disposition"] = f"attachment; filename=scene_descriptions_{session_id}.txt"
        response.headers["Content-Type"] = "text/plain"
        return response
    except Exception as e:
        print(f"Error downloading scene descriptions: {e}")
        return "Error generating scene descriptions file", 500

if __name__ == '__main__':
    # We don't need to start a new session here as it will be created when needed
    # The session_history.init() call earlier already initializes the module
    
    # Run the Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
