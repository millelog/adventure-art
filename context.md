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


"""
character_store.py

Module to manage character data storage, including character descriptions.
"""

import os
import json
from pathlib import Path

# Get the base directory for character data storage
CHARACTER_DATA_DIR = os.getenv('CHARACTER_DATA_PATH', 'character_data')

# Ensure the character data directory exists
os.makedirs(CHARACTER_DATA_DIR, exist_ok=True)

def get_character_file_path():
    """Get the path to the character data JSON file."""
    return os.path.join(CHARACTER_DATA_DIR, 'characters.json')

def load_characters():
    """Load all character data from the JSON file."""
    file_path = get_character_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {}

def save_characters(characters):
    """Save character data to the JSON file."""
    with open(get_character_file_path(), 'w') as f:
        json.dump(characters, f, indent=2)

def add_or_update_character(character_id, data):
    """
    Adds a new character or updates an existing character's data.
    
    Parameters:
        character_id (str): The unique identifier (or name) of the character.
        data (dict): A dictionary with character details (name and description).
    
    Returns:
        The updated dictionary of all characters.
    """
    characters = load_characters()
    characters[character_id] = data
    save_characters(characters)
    return characters

def remove_character(character_id):
    """
    Removes a character.
    
    Parameters:
        character_id (str): The unique identifier of the character to remove.
    
    Returns:
        bool: True if character was found and removed, False otherwise.
    """
    characters = load_characters()
    if character_id in characters:
        del characters[character_id]
        save_characters(characters)
        return True
    return False

def get_character(character_id):
    """Get a single character's data."""
    characters = load_characters()
    return characters.get(character_id)

def get_all_characters():
    """Get all characters' data."""
    return load_characters()

# Example usage:
if __name__ == "__main__":
    # Add or update a character
    char_id = "wizard_001"
    char_data = {
        "name": "Gandalf",
        "description": "A wise old wizard with a long white beard."
    }
    add_or_update_character(char_id, char_data)


"""
config.py

Central configuration settings for the server.
Override any default values by setting environment variables.
"""

import os
import sys
from pathlib import Path

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable is not set!")
    print("Please check that:")
    print("1. Your .env file exists in the project root directory")
    print("2. It contains a valid OPENAI_API_KEY")
    print("3. The application has permission to read the file")
    sys.exit(1)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY environment variable is not set!")
    print("Please check that:")
    print("1. Your .env file exists in the project root directory")
    print("2. It contains a valid GEMINI_API_KEY")
    print("3. The application has permission to read the file")
    sys.exit(1)

# Get project root directory
project_root = Path(__file__).resolve().parent.parent.parent

# File-based character store configuration
CHARACTER_DATA_PATH = os.environ.get('CHARACTER_DATA_PATH', 
    str(project_root / 'adventure_art' / 'server' / 'character_data'))

# File-based environment store configuration - using the same base directory as characters
ENVIRONMENT_DATA_PATH = CHARACTER_DATA_PATH

# Flask and SocketIO configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')  # Make sure to change in production
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

"""
environment_analyzer.py

Module to analyze transcripts and update environment descriptions based on new information.
Uses OpenAI GPT-4o to detect significant environmental changes.
"""

import openai
import json
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import environment_store
from adventure_art.server import scene_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# This will be imported from app.py to avoid circular imports
emit_environment_update = None

def set_emit_callback(callback_function):
    """Set the callback function for emitting environment updates."""
    global emit_environment_update
    emit_environment_update = callback_function

def analyze_transcript(transcript):
    """
    Analyzes a transcript to determine if the environment description needs to be updated.
    
    Parameters:
        transcript (str): The transcribed text to analyze.
        
    Returns:
        updated_environment (str): The updated environment description if an update is needed, 
                                  or None if no update is needed.
    """
    # Check if environment is locked against automatic updates
    if environment_store.is_environment_locked():
        print("Environment is locked, skipping automatic update")
        return None
        
    # Check if we have a valid transcript
    if not transcript or len(transcript.strip()) < 3:
        print("No valid transcript to analyze for environment updates")
        return None
    
    # Get the current environment description
    current_environment = environment_store.get_environment()
    current_description = current_environment.get('description', '')
    
    # Get the previous scene prompt for context
    previous_prompt = scene_store.get_last_prompt()
    previous_prompt_section = ""
    if previous_prompt:
        previous_prompt_section = (
            "Previous Scene Description:\n"
            f"{previous_prompt}\n\n"
            "Consider the previous scene description as additional context, but prioritize the transcript "
            "for determining if the environment has changed significantly."
        )
    
    # Define the function for structured output
    functions = [
        {
            "name": "update_environment",
            "description": "Update the environment description based on transcript analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "needs_update": {
                        "type": "boolean",
                        "description": "Whether the environment needs to be updated based on the transcript"
                    },
                    "environment_description": {
                        "type": "string",
                        "description": "The new environment description (only if needs_update is true). Must ONLY describe the physical setting (location, atmosphere, time of day, weather, terrain features) without ANY characters, actions, or narrative elements."
                    }
                },
                "required": ["needs_update"]
            }
        }
    ]
    
    # Build the prompt for the language model
    system_message = (
        "You analyze D&D session transcripts to maintain an accurate environment description. "
        "You only update the description when there's clear evidence of a significant location/setting change. "
        "IMPORTANT: Environment descriptions must NEVER include characters, actions, or narrative elements - "
        "they should ONLY describe the physical setting itself (location, atmosphere, time of day, weather, terrain). "
        "Your output should be structured using the function provided."
    )
    
    user_message = (
        "You are an environment analyzer for a D&D game. Your job is to maintain a concise description of the current "
        "environment or setting where the game is taking place. You'll analyze new transcript snippets to determine if "
        "the environment has changed significantly, and if so, how to update the description.\n\n"
        "Guidelines:\n"
        "- Keep the environment description brief (under 100 words) but informative\n"
        "- Focus ONLY on physical setting elements that would appear in an image (location, atmosphere, time of day, weather, etc.)\n"
        "- NEVER include characters, character actions, or narrative elements in the environment description\n"
        "- The environment description should be universally applicable regardless of what characters are doing in the scene\n"
        "- Only update the description if there's clear evidence in the transcript that the setting has changed\n"
        "- Maintain consistency with previous descriptions unless directly contradicted\n"
        "- Be conservative about making changes - don't change the environment for minor details\n\n"
        "Current Environment Description:\n"
        f"{current_description}\n\n"
        + (f"{previous_prompt_section}\n\n" if previous_prompt else "")
        + "New Transcript Snippet:\n"
        f"{transcript}\n\n"
        "Analyze this transcript and determine if the environment has changed significantly. "
        "If yes, provide a new complete environment description that ONLY describes the physical setting. "
        "If no, indicate no update is needed."
    )
    
    try:
        # Call the OpenAI chat completion API with function calling
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            functions=functions,
            function_call={"name": "update_environment"},
            max_tokens=500,
            temperature=0.3  # Lower temperature for more conservative updates
        )
        
        # Extract the function call arguments
        function_args = json.loads(response.choices[0].message.function_call.arguments)
        
        # Check if update is needed
        if not function_args.get("needs_update", False):
            print("No environment update needed")
            return None
        else:
            # Get the new environment description
            new_description = function_args.get("environment_description", "").strip()
            
            if not new_description:
                print("No valid environment description provided")
                return None
                
            # Additional check to filter out character names and actions
            if contains_character_elements(new_description, transcript):
                print("Environment description contains character elements, filtering...")
                new_description = filter_character_elements(new_description)
                
            print("Updating environment description")
            # Update the environment store
            environment_store.update_environment(new_description)
            
            # Emit the update via socket if the callback is set
            if emit_environment_update:
                emit_environment_update(new_description)
                
            return new_description
            
    except Exception as e:
        print(f"Error analyzing environment: {e}")
        return None

def contains_character_elements(description, transcript):
    """
    Check if the environment description contains character names or actions.
    This is a simple heuristic check that can be improved.
    
    Parameters:
        description (str): The environment description to check
        transcript (str): The original transcript to compare against
        
    Returns:
        bool: True if character elements are detected, False otherwise
    """
    # Extract potential character names from transcript (words starting with uppercase)
    words = transcript.split()
    potential_names = [word for word in words if word and word[0].isupper() and len(word) > 2]
    
    # Check if any potential names appear in the description
    for name in potential_names:
        if name in description:
            return True
    
    # Check for action verbs that might indicate character actions
    action_verbs = ["leads", "walks", "runs", "sits", "stands", "moves", "travels", "fights", "speaks"]
    for verb in action_verbs:
        if f" {verb} " in f" {description} ":
            return True
            
    return False

def filter_character_elements(description):
    """
    Attempt to filter out character elements from the environment description.
    This is a simple implementation that can be improved.
    
    Parameters:
        description (str): The environment description to filter
        
    Returns:
        str: The filtered environment description
    """
    # Split into sentences
    sentences = description.split('. ')
    filtered_sentences = []
    
    for sentence in sentences:
        # Skip sentences that likely contain character actions
        action_verbs = ["leads", "walks", "runs", "sits", "stands", "moves", "travels", "fights", "speaks"]
        if any(f" {verb} " in f" {sentence.lower()} " for verb in action_verbs):
            continue
            
        filtered_sentences.append(sentence)
    
    # If we filtered everything, return a generic version of the first sentence
    if not filtered_sentences and sentences:
        first_sentence = sentences[0]
        # Try to extract just the environment part
        if "with" in first_sentence:
            return first_sentence.split("with")[0].strip() + "."
        else:
            return first_sentence + "."
    
    return '. '.join(filtered_sentences) + ('.' if filtered_sentences and not filtered_sentences[-1].endswith('.') else '')

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party leaves the dark forest and emerges onto a vast open plain. The sun is setting, "
        "casting long shadows across the tall grass. In the distance, mountains can be seen."
    )
    updated_env = analyze_transcript(sample_transcript)
    print("Updated Environment:" if updated_env else "No update needed")
    if updated_env:
        print(updated_env) 


"""
environment_store.py

Module to manage environment data storage, including environment descriptions
and a lock flag to prevent automatic updates.
"""

import os
import json
from pathlib import Path
from adventure_art.server.config import ENVIRONMENT_DATA_PATH

# Get the base directory for environment data storage
CHARACTER_DATA_DIR = ENVIRONMENT_DATA_PATH

# Ensure the environment data directory exists
os.makedirs(CHARACTER_DATA_DIR, exist_ok=True)

def get_environment_file_path():
    """Get the path to the environment data JSON file."""
    return os.path.join(CHARACTER_DATA_DIR, 'environment.json')

def load_environment():
    """Load environment data from the JSON file."""
    file_path = get_environment_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    # Default environment with empty description and unlocked
    return {
        "description": "A generic fantasy setting with no specific details yet.",
        "locked": False
    }

def save_environment(environment_data):
    """Save environment data to the JSON file."""
    with open(get_environment_file_path(), 'w') as f:
        json.dump(environment_data, f, indent=2)

def update_environment(description, locked=None):
    """
    Updates the environment description and optionally the lock status.
    
    Parameters:
        description (str): The new environment description.
        locked (bool, optional): If provided, updates the lock status.
    
    Returns:
        The updated environment data dictionary.
    """
    environment = load_environment()
    
    # Update description if provided and not locked
    if description and (not environment.get('locked', False) or locked is not None):
        environment['description'] = description
    
    # Update lock status if provided
    if locked is not None:
        environment['locked'] = locked
    
    save_environment(environment)
    return environment

def get_environment():
    """Get the current environment data."""
    return load_environment()

def is_environment_locked():
    """Check if the environment is locked against automatic updates."""
    environment = load_environment()
    return environment.get('locked', False)

# Example usage:
if __name__ == "__main__":
    # Update environment description
    env_data = update_environment("A dark forest with tall trees blocking most of the sunlight.")
    print("Updated environment:", env_data) 


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


"""
image_generator.py

Module to generate an image based on a scene description using the Google Imagen 3.0 API.
It receives a textual scene description and returns the URL of the generated image.
"""

import os
from google import genai
from google.genai import types
import base64
from io import BytesIO
import tempfile
from pathlib import Path

# Get the API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Initialize the Gen AI client
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_image(scene_description):
    """
    Generates an image based on the provided scene description using the Google Imagen 3.0 API.
    Returns None if no valid scene description is provided or if image generation fails.
    
    Parameters:
        scene_description (str): A detailed narrative description of the scene.
    
    Returns:
        image_url (str): Path to the locally saved generated image.
        None: If image generation fails or no valid description is provided.
    """
    if not scene_description:
        print("No valid scene description provided for image generation")
        return None
        
    try:
        # Generate image using Imagen 3.0
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=scene_description,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='16:9',  # Using widescreen ratio for better scene composition
            )
        )

        # Save the generated image to a temporary file
        if response.generated_images:
            # Create a temporary file with a .png extension
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                # Get the first generated image
                image_bytes = response.generated_images[0].image.image_bytes
                temp_file.write(image_bytes)
                return temp_file.name
        else:
            print("No images were generated")
            return None

    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Example usage for testing:
if __name__ == "__main__":
    sample_description = (
        "A dark, stormy night with a looming castle in the distance, "
        "illuminated by flashes of lightning, and a brave warrior standing guard."
    )
    try:
        path = generate_image(sample_description)
        print("Generated image saved at:", path)
    except Exception as error:
        print("Error:", error)

"""
scene_composer.py

Module to generate a detailed narrative scene description based on a transcript and
stored character details. This module retrieves character data from the file-based
character store and composes a prompt for the OpenAI language model.
"""

import openai
import re
import json
import random  # Add import for randomization
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import character_store
from adventure_art.server import environment_store
from adventure_art.server import scene_store
from adventure_art.server import style_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def compose_scene(transcript):
    """
    Composes a focused scene description based on the session transcript and stored character details.
    Identifies a key event and generates a concise description optimized for image generation.
    Provides all character details to the language model which will determine relevance.
    Returns None if no valid scene can be composed.
    
    Parameters:
        transcript (str): The transcribed text of the D&D session.
    
    Returns:
        scene_description (str): A concise, focused description of the key event in the scene.
        None: If no valid scene can be composed.
    """
    # Check if we have a valid transcript
    if not transcript or len(transcript.strip()) < 3:
        print("No valid transcript to compose scene from")
        return None
        
    # Basic validation to check if transcript seems to be in English
    common_english_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'is', 'are', 'and'}
    words = set(transcript.lower().split())
    if not any(word in common_english_words for word in words):
        print("Transcript appears to be non-English or invalid")
        return None
    
    # Retrieve all character data
    all_characters = character_store.get_all_characters()
    
    # Format all character details as a list and shuffle it for randomization
    character_details = []
    for char_id, data in all_characters.items():
        char_desc = f"{data.get('name', char_id)}: {data.get('description', 'No description provided')}"
        character_details.append(char_desc)
    
    # Randomize the order of character details to avoid positional bias
    random.shuffle(character_details)
    
    if character_details:
        character_details_text = "\n\n".join(character_details)
    else:
        character_details_text = "No character data available."
    
    # Get the current environment description
    environment_data = environment_store.get_environment()
    environment_description = environment_data.get('description', 'No specific environment defined.')
    
    # Get the previous scene prompt for continuity
    previous_prompt = scene_store.get_last_prompt()
    previous_prompt_section = ""
    if previous_prompt:
        previous_prompt_section = (
            "Previous Scene Description:\n"
            f"{previous_prompt}\n\n"
            "Use the previous scene description to maintain visual consistency where appropriate, "
            "but focus on the new action or moment described in the current transcript."
        )
    
    # Get the style directive
    style_directive = style_store.get_style_directive()
    
    # Define the function for structured output
    functions = [
        {
            "name": "generate_scene_description",
            "description": "Generate a focused scene description based on the transcript",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene_description": {
                        "type": "string",
                        "description": "A concise, focused description of the key event in the scene, optimized for image generation. Should be under 200 words and focus on one key moment or action."
                    },
                    "character_names": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of character names that appear in the scene description."
                    }
                },
                "required": ["scene_description", "character_names"]
            }
        }
    ]
    
    # Build the prompt for the language model with specific constraints
    system_message = (
        "You are a concise D&D scene descriptor focused on clear, imageable moments. "
        "Only include characters that are actually mentioned or implied in the transcript, maintaining consistency with their descriptions "
        "and ensuring the scene is set within the provided environment. Your output should be structured using the function provided. "
        "Always use character names explicitly in your descriptions to maintain character consistency across scenes."
    )
    
    user_message = (
        "You are a focused scene descriptor for a D&D session. Your task is to identify the most visually interesting "
        "key event from the transcript and describe it in a clear, concise way that's optimized for image generation.\n\n"
        "Guidelines:\n"
        "- Focus on ONE key moment or action\n"
        "- Only include characters that are actually mentioned or implied in the transcript\n"
        "- ALWAYS use character names explicitly in your description, even if they're only implied in the transcript\n"
        "- If a character is referenced indirectly in the transcript (e.g., 'the wizard'), use their proper name (e.g., 'Gandalf')\n"
        "- Keep descriptions under 200 words\n"
        "- Use clear, specific visual language\n"
        "- Prioritize action and emotion over complex details\n"
        "- For any characters you include, maintain consistency with their provided descriptions\n"
        "- If no clear action is described, create a simple portrait or scene of the mentioned characters\n"
        "- Avoid complex lighting or camera instructions\n"
        "- Make the scene consistent with the current environment description\n"
        f"- {'' if not previous_prompt else 'Maintain visual continuity with the previous scene where appropriate'}\n\n"
        "Visual Style Guidelines:\n"
        f"{style_directive}\n\n"
        "Current Environment:\n"
        f"{environment_description}\n\n"
        + (f"{previous_prompt_section}\n\n" if previous_prompt else "")
        + "Available Characters:\n"
        f"{character_details_text}\n\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        "Generate a concise scene description, only including characters that are relevant to this specific moment and ensuring "
        "it fits within the described environment. Always refer to characters by their proper names to maintain consistency."
    )
    
    try:
        # Call the OpenAI chat completion API with function calling
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            functions=functions,
            function_call={"name": "generate_scene_description"},
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract the function call arguments
        function_args = json.loads(response.choices[0].message.function_call.arguments)
        
        # Get the scene description
        scene_description = function_args.get("scene_description", "").strip()
        
        # Get the character names (for potential future use)
        character_names = function_args.get("character_names", [])
        
        if not scene_description:
            print("No valid scene description generated")
            return None
        
        # Store the scene description for future reference
        scene_store.update_last_prompt(scene_description)
        
        return scene_description
        
    except Exception as e:
        print(f"Error generating scene description: {e}")
        return None

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party enters a dimly lit tavern. Gandalf sits in the corner, quietly observing the newcomers."
    )
    description = compose_scene(sample_transcript)
    print("Generated Scene Description:")
    print(description)

"""
scene_store.py

Module to manage scene data storage, including the most recent scene prompt.
This helps maintain consistency between consecutive scene generations.
"""

import os
import json
from pathlib import Path
from adventure_art.server.config import CHARACTER_DATA_PATH

# Get the base directory for scene data storage (using the same base as character data)
SCENE_DATA_DIR = CHARACTER_DATA_PATH

# Ensure the scene data directory exists
os.makedirs(SCENE_DATA_DIR, exist_ok=True)

def get_scene_file_path():
    """Get the path to the scene data JSON file."""
    return os.path.join(SCENE_DATA_DIR, 'scene_data.json')

def load_scene_data():
    """Load scene data from the JSON file."""
    file_path = get_scene_file_path()
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    # Default scene data with empty prompt
    return {
        "last_prompt": "",
        "timestamp": 0
    }

def save_scene_data(scene_data):
    """Save scene data to the JSON file."""
    with open(get_scene_file_path(), 'w') as f:
        json.dump(scene_data, f, indent=2)

def update_last_prompt(prompt, timestamp=None):
    """
    Updates the last scene prompt.
    
    Parameters:
        prompt (str): The scene prompt used for generation.
        timestamp (int, optional): Timestamp of when the scene was generated.
    
    Returns:
        The updated scene data dictionary.
    """
    import time
    scene_data = load_scene_data()
    
    # Update prompt
    scene_data['last_prompt'] = prompt
    
    # Update timestamp if provided, otherwise use current time
    scene_data['timestamp'] = timestamp or int(time.time())
    
    save_scene_data(scene_data)
    return scene_data

def get_last_prompt():
    """Get the most recent scene prompt."""
    scene_data = load_scene_data()
    return scene_data.get('last_prompt', "")

# Example usage:
if __name__ == "__main__":
    # Update last prompt
    scene_data = update_last_prompt("A dark forest with tall trees blocking most of the sunlight.")
    print("Updated scene data:", scene_data) 


"""
session_history.py

Module to track and store the history of a session, including:
- Transcripts
- Scene descriptions (prompts)
- Generated image paths
- Timestamps

The history is stored in a JSON file that is created when the server starts
and continuously updated as new events occur during the session.
"""

import os
import json
import time
import uuid
import shutil
from datetime import datetime
from pathlib import Path

# Directory to store session history files
HISTORY_DIR = Path(__file__).resolve().parent / 'session_history'
HISTORY_IMAGES_DIR = HISTORY_DIR / 'images'

# Ensure the history directories exist
try:
    HISTORY_DIR.mkdir(exist_ok=True)
    HISTORY_IMAGES_DIR.mkdir(exist_ok=True)
    print(f"Session history directories created/verified at {HISTORY_DIR}")
except Exception as e:
    print(f"Warning: Could not create session history directories: {e}")
    # Fallback to a temporary directory if needed
    try:
        import tempfile
        temp_dir = tempfile.gettempdir()
        HISTORY_DIR = Path(temp_dir) / 'adventure_art_session_history'
        HISTORY_IMAGES_DIR = HISTORY_DIR / 'images'
        HISTORY_DIR.mkdir(exist_ok=True)
        HISTORY_IMAGES_DIR.mkdir(exist_ok=True)
        print(f"Using fallback session history directories at {HISTORY_DIR}")
    except Exception as e2:
        print(f"Critical error: Could not create fallback session history directories: {e2}")

# Current session ID and history
current_session_id = None
current_session_file = None
session_history = []

def init():
    """
    Initialize the session history module.
    This function is called when the module is imported.
    It ensures that the module is properly initialized without causing errors.
    """
    global current_session_id, current_session_file, session_history
    
    try:
        # Make sure the directories exist
        HISTORY_DIR.mkdir(exist_ok=True)
        HISTORY_IMAGES_DIR.mkdir(exist_ok=True)
        
        # Initialize the session variables
        current_session_id = None
        current_session_file = None
        session_history = []
        
        print("Session history module initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing session history module: {e}")
        return False

# Initialize the module
init_success = init()

def start_new_session():
    """
    Start a new session with a unique ID.
    Creates a new JSON file for storing the session history.
    
    Returns:
        str: The session ID
    """
    global current_session_id, current_session_file, session_history
    
    try:
        # Generate a unique session ID using timestamp and UUID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        current_session_id = f"{timestamp}_{unique_id}"
        
        # Create a new session file
        current_session_file = HISTORY_DIR / f"session_{current_session_id}.json"
        
        # Initialize the session history
        session_history = []
        
        # Create the session-specific image directory
        session_image_dir = HISTORY_IMAGES_DIR / current_session_id
        session_image_dir.mkdir(exist_ok=True)
        
        # Save the initial session data
        session_data = {
            "session_id": current_session_id,
            "start_time": datetime.now().isoformat(),
            "events": session_history
        }
        
        with open(current_session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        print(f"Started new session: {current_session_id}")
        return current_session_id
    except Exception as e:
        print(f"Error starting new session: {e}")
        # If we can't create a new session, try to use the most recent one
        try:
            sessions = get_all_sessions()
            if sessions:
                most_recent = sessions[0]  # Sessions are sorted newest first
                current_session_id = most_recent["session_id"]
                current_session_file = HISTORY_DIR / f"session_{current_session_id}.json"
                print(f"Using existing session: {current_session_id}")
                return current_session_id
        except Exception as e2:
            print(f"Error finding existing session: {e2}")
        
        # If all else fails, use a temporary session ID
        current_session_id = f"temp_{str(uuid.uuid4())[:8]}"
        print(f"Using temporary session ID: {current_session_id}")
        return current_session_id

def add_scene_event(transcript, prompt, original_image_path):
    """
    Add a complete scene event to the session history.
    This combines transcript, prompt, and image into a single event.
    
    Parameters:
        transcript (str): The transcribed text
        prompt (str): The scene description prompt
        original_image_path (str): Path to the original image
        
    Returns:
        str: Path to the copied image in the history directory
    """
    if not current_session_id:
        start_new_session()
    
    # Create a filename for the copied image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_filename = f"image_{timestamp}.png"
    
    # Path to store the image in the session history
    session_image_dir = HISTORY_IMAGES_DIR / current_session_id
    history_image_path = session_image_dir / image_filename
    
    # Copy the image to the history directory
    try:
        shutil.copy2(original_image_path, history_image_path)
        relative_path = f"session_history/images/{current_session_id}/{image_filename}"
        
        event = {
            "type": "scene",
            "timestamp": datetime.now().isoformat(),
            "transcript": transcript,
            "prompt": prompt,
            "image_path": str(relative_path)
        }
        
        _add_event(event)
        return str(relative_path)
    except Exception as e:
        print(f"Error copying image to history: {e}")
        return None

def _add_event(event):
    """
    Add an event to the session history and save to the JSON file.
    
    Parameters:
        event (dict): The event to add
    """
    global session_history
    
    if not current_session_id:
        # If no session exists, start a new one
        start_new_session()
    
    # Add the event to the in-memory history
    session_history.append(event)
    
    # Update the JSON file
    try:
        # Check if the session file exists
        if current_session_file and current_session_file.exists():
            # Read the existing data first
            try:
                with open(current_session_file, 'r') as f:
                    session_data = json.load(f)
                # Update the events
                session_data["events"] = session_history
            except (json.JSONDecodeError, FileNotFoundError):
                # If the file is corrupted or doesn't exist, create new data
                session_data = {
                    "session_id": current_session_id,
                    "start_time": datetime.now().isoformat(),
                    "events": session_history
                }
        else:
            # Create new session data
            session_data = {
                "session_id": current_session_id,
                "start_time": datetime.now().isoformat(),
                "events": session_history
            }
        
        # Write the updated data
        with open(current_session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        print(f"Error saving session history: {e}")
        # Don't raise the exception, just log it

def get_current_session_id():
    """
    Get the current session ID.
    
    Returns:
        str: The current session ID
    """
    if not current_session_id:
        start_new_session()
    return current_session_id

def get_session_history():
    """
    Get the current session history.
    
    Returns:
        list: The session history events
    """
    return session_history

def get_all_sessions():
    """
    Get a list of all session IDs.
    
    Returns:
        list: List of session IDs
    """
    sessions = []
    for file in HISTORY_DIR.glob("session_*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id"),
                    "start_time": data.get("start_time"),
                    "event_count": len(data.get("events", []))
                })
        except Exception as e:
            print(f"Error reading session file {file}: {e}")
    
    # Sort by start time (newest first)
    sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    return sessions

def get_session_by_id(session_id):
    """
    Get a specific session by ID.
    
    Parameters:
        session_id (str): The session ID
        
    Returns:
        dict: The session data or None if not found
    """
    session_file = HISTORY_DIR / f"session_{session_id}.json"
    if session_file.exists():
        try:
            with open(session_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading session file {session_file}: {e}")
    return None 

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

"""
transcribe.py

Module to transcribe audio using a local Whisper large model.
This module loads the Whisper model once and uses it to transcribe
audio files provided as file-like objects.
"""

import whisper
import tempfile
import os
import torch

# Check if CUDA is available and set the device accordingly
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {DEVICE}")

# Load the local Whisper large model (this might take a moment at startup)
model = None

def get_model():
    """Get or initialize the Whisper model."""
    global model
    if model is None:
        print("Loading Whisper large model...")
        model = whisper.load_model("large").to(DEVICE)
        print("Model loaded successfully")
    return model

def transcribe_audio(audio_file):
    """
    Transcribes an audio file using the local Whisper large model.
    
    Parameters:
        audio_file: A file-like object containing audio data (e.g., WAV format).
    
    Returns:
        A string containing the transcribed text.
    """
    # Save the uploaded audio to a temporary file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio_file.read())
            tmp_path = tmp.name
    except Exception as e:
        raise Exception(f"Error saving audio to temporary file: {e}")
    
    try:
        # Use Whisper to transcribe the audio from the temporary file
        result = get_model().transcribe(tmp_path, fp16=torch.cuda.is_available())  # Enable fp16 if using GPU
        transcript = result.get("text", "")
    except Exception as e:
        raise Exception(f"Error during transcription: {e}")
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    
    return transcript


#!/usr/bin/env python3
"""
recorder.py

Captures live audio from the laptop's microphone, slices it into chunks of a configurable duration,
and sends each chunk to the server for processing via an HTTP POST request.
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import io
import time
import threading

# Configuration
CHUNK_DURATION = 30       # Duration of each audio chunk in seconds
SAMPLE_RATE = 44100       # Standard sample rate for audio recording
CHANNELS = 1              # Number of audio channels (1 for mono, 2 for stereo)

# Replace with the actual URL and port of your server
SERVER_URL = "http://localhost:5000/upload_audio"


def send_audio_chunk(audio_data):
    """Send audio chunk to server in a separate thread."""
    # Write the recorded audio to an in-memory buffer as a WAV file
    buffer = io.BytesIO()
    try:
        sf.write(buffer, audio_data, SAMPLE_RATE, format='WAV')
        buffer.seek(0)  # Reset buffer position to the beginning
    except Exception as e:
        print("Error writing audio to buffer:", e)
        return
    
    print("Sending audio chunk to server...")
    files = {'audio': ('chunk.wav', buffer, 'audio/wav')}
    try:
        response = requests.post(SERVER_URL, files=files)
        print("Server response:", response.status_code, response.text)
    except Exception as e:
        print("Error sending audio chunk:", e)


def record_and_send():
    print("Starting live audio capture...")
    
    while True:
        print(f"Recording audio for {CHUNK_DURATION} seconds...")
        try:
            # Record audio: This returns a NumPy array of shape (samples, channels)
            audio_data = sd.rec(int(CHUNK_DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS)
            sd.wait()  # Block until recording is finished
        except Exception as e:
            print("Error during recording:", e)
            continue
        
        # Start a new thread to send the audio chunk
        sender_thread = threading.Thread(target=send_audio_chunk, args=(audio_data,))
        sender_thread.start()
        
        # Continue with the next recording immediately
        # The sender thread will handle the upload in the background


if __name__ == '__main__':
    record_and_send()


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Adventure Art - Session History</title>
    <style>
        :root {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --accent: #6d28d9;
            --accent-hover: #7c3aed;
            --border: #404040;
            --error: #ef4444;
            --success: #10b981;
            --transcript-color: #3498db;
            --prompt-color: #2ecc71;
            --image-color: #e74c3c;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0;
            padding: 0;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }

        h1, h2, h3 {
            color: var(--text-primary);
        }

        h1 {
            text-align: center;
            margin: 20px 0;
            font-size: 2.5rem;
            font-weight: 700;
        }

        h2 {
            margin-bottom: 20px;
        }

        /* Navigation */
        .nav-tabs {
            display: flex;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
            background-color: var(--bg-secondary);
            border-radius: 8px 8px 0 0;
            padding: 0 10px;
        }

        .nav-tab {
            padding: 15px 25px;
            cursor: pointer;
            border: 1px solid transparent;
            margin-bottom: -1px;
            color: var(--text-secondary);
            transition: all 0.3s ease;
            border-radius: 8px 8px 0 0;
            text-decoration: none;
        }

        .nav-tab:hover {
            color: var(--text-primary);
            background-color: rgba(255, 255, 255, 0.05);
        }

        .nav-tab.active {
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-bottom-color: var(--bg-primary);
            background-color: var(--bg-primary);
        }

        /* Session list styles */
        .session-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .session-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }

        .session-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
        }

        .session-card h3 {
            margin-bottom: 10px;
            color: var(--text-primary);
        }

        .session-card p {
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        /* Session detail styles */
        .back-button {
            display: inline-flex;
            align-items: center;
            margin-bottom: 20px;
            padding: 10px 20px;
            background-color: var(--accent);
            color: white;
            border-radius: 6px;
            text-decoration: none;
            transition: background-color 0.2s;
            border: none;
            cursor: pointer;
            font-size: 1rem;
        }

        .back-button:hover {
            background-color: var(--accent-hover);
        }

        .scene-card {
            margin-bottom: 30px;
            border-radius: 8px;
            background-color: var(--bg-secondary);
            border: 1px solid var(--border);
            overflow: hidden;
        }

        .scene-image {
            width: 100%;
            cursor: pointer;
            transition: transform 0.3s ease;
        }

        .scene-image:hover {
            transform: scale(1.01);
        }

        .scene-content {
            padding: 20px;
        }

        .scene-timestamp {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin-bottom: 15px;
        }

        .scene-details {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .detail-section {
            border-radius: 6px;
            padding: 15px;
            background-color: var(--bg-primary);
            border: 1px solid var(--border);
        }

        .detail-section h4 {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 10px;
            color: var(--text-primary);
            font-size: 1rem;
            cursor: pointer;
        }

        .detail-section .indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .transcript-section .indicator {
            background-color: var(--transcript-color);
        }

        .prompt-section .indicator {
            background-color: var(--prompt-color);
        }

        .detail-content {
            color: var(--text-secondary);
            line-height: 1.6;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease, padding-top 0.3s ease;
        }

        .detail-content.expanded {
            max-height: 500px;
            padding-top: 10px;
        }

        .toggle-icon {
            margin-left: auto;
            transition: transform 0.3s ease;
        }

        .expanded .toggle-icon {
            transform: rotate(180deg);
        }

        /* Fullscreen image modal */
        .image-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .modal-content {
            max-width: 90%;
            max-height: 90%;
        }

        .close-modal {
            position: absolute;
            top: 20px;
            right: 20px;
            color: white;
            font-size: 30px;
            cursor: pointer;
            background: rgba(0, 0, 0, 0.5);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Loading and error states */
        .loading, .no-sessions, .error {
            text-align: center;
            padding: 40px;
            font-size: 1.2em;
            color: var(--text-secondary);
            background-color: var(--bg-secondary);
            border-radius: 8px;
            border: 1px solid var(--border);
        }

        .error {
            color: var(--error);
        }

        /* Download buttons */
        .download-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }

        .download-button {
            display: inline-flex;
            align-items: center;
            padding: 10px 15px;
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 6px;
            text-decoration: none;
            transition: all 0.2s;
            cursor: pointer;
            font-size: 0.9rem;
        }

        .download-button:hover {
            background-color: var(--accent);
            border-color: var(--accent);
        }

        .download-button svg {
            margin-right: 8px;
        }

        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }

            .session-list {
                grid-template-columns: 1fr;
            }

            .nav-tab {
                padding: 10px 15px;
                font-size: 0.9rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Adventure Art - Session History</h1>
        
        <div class="nav-tabs">
            <a href="/" class="nav-tab">Home</a>
            <div class="nav-tab active">Session History</div>
        </div>
        
        <div id="sessions-view">
            <h2>All Sessions</h2>
            <div id="session-list" class="session-list">
                <div class="loading">Loading sessions...</div>
            </div>
        </div>
        
        <div id="session-detail-view" style="display: none;">
            <button class="back-button" id="back-button">← Back to All Sessions</button>
            <h2 id="session-title">Session Details</h2>
            
            <div class="download-buttons">
                <a href="#" id="download-transcripts" class="download-button" target="_blank">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 16L12 8M12 16L9 13M12 16L15 13M19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Download All Transcripts
                </a>
                <a href="#" id="download-scene-descriptions" class="download-button" target="_blank">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 16L12 8M12 16L9 13M12 16L15 13M19 21H5C3.89543 21 3 20.1046 3 19V5C3 3.89543 3.89543 3 5 3H19C20.1046 3 21 3.89543 21 5V19C21 20.1046 20.1046 21 19 21Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Download All Scene Descriptions
                </a>
            </div>
            
            <div id="session-events"></div>
        </div>
    </div>

    <!-- Fullscreen image modal -->
    <div id="image-modal" class="image-modal">
        <span class="close-modal" id="close-modal">&times;</span>
        <img id="modal-image" class="modal-content">
    </div>

    <script>
        // Fetch all sessions when the page loads
        document.addEventListener('DOMContentLoaded', fetchSessions);
        
        // Add event listener for back button
        document.getElementById('back-button').addEventListener('click', function(e) {
            e.preventDefault();
            showSessionsView();
        });
        
        // Modal handling
        const modal = document.getElementById('image-modal');
        const modalImg = document.getElementById('modal-image');
        const closeModal = document.getElementById('close-modal');
        
        closeModal.addEventListener('click', function() {
            modal.style.display = 'none';
        });
        
        // Close modal when clicking outside the image
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        function fetchSessions() {
            fetch('/sessions')
                .then(response => response.json())
                .then(sessions => {
                    const sessionList = document.getElementById('session-list');
                    sessionList.innerHTML = '';
                    
                    if (sessions.length === 0) {
                        sessionList.innerHTML = '<div class="no-sessions">No sessions found</div>';
                        return;
                    }
                    
                    sessions.forEach(session => {
                        const sessionCard = document.createElement('div');
                        sessionCard.className = 'session-card';
                        sessionCard.dataset.id = session.session_id;
                        
                        // Format the date
                        const date = new Date(session.start_time);
                        const formattedDate = date.toLocaleString();
                        
                        sessionCard.innerHTML = `
                            <h3>Session ${session.session_id.split('_')[0]}</h3>
                            <p><strong>Started:</strong> ${formattedDate}</p>
                            <p><strong>Scenes:</strong> ${session.event_count}</p>
                        `;
                        
                        sessionCard.addEventListener('click', function() {
                            fetchSessionDetail(session.session_id);
                        });
                        
                        sessionList.appendChild(sessionCard);
                    });
                })
                .catch(error => {
                    console.error('Error fetching sessions:', error);
                    document.getElementById('session-list').innerHTML = 
                        '<div class="error">Error loading sessions. Please try again later.</div>';
                });
        }
        
        function fetchSessionDetail(sessionId) {
            fetch(`/sessions/${sessionId}`)
                .then(response => response.json())
                .then(session => {
                    // Update the session title
                    const date = new Date(session.start_time);
                    document.getElementById('session-title').textContent = 
                        `Session: ${session.session_id.split('_')[0]} (${date.toLocaleString()})`;
                    
                    // Update download links
                    document.getElementById('download-transcripts').href = `/sessions/${session.session_id}/download/transcripts`;
                    document.getElementById('download-scene-descriptions').href = `/sessions/${session.session_id}/download/scene_descriptions`;
                    
                    // Clear previous events
                    const eventsContainer = document.getElementById('session-events');
                    eventsContainer.innerHTML = '';
                    
                    // Add each scene event
                    session.events.forEach(event => {
                        if (event.type === 'scene') {
                            const sceneCard = document.createElement('div');
                            sceneCard.className = 'scene-card';
                            
                            // Format timestamp
                            const timestamp = new Date(event.timestamp).toLocaleString();
                            
                            // Create the image section
                            const imageHtml = `
                                <img src="/${event.image_path}" alt="Generated scene" 
                                     class="scene-image" onclick="openImageModal(this.src)">
                            `;
                            
                            // Create the content section
                            const contentHtml = `
                                <div class="scene-content">
                                    <div class="scene-timestamp">${timestamp}</div>
                                    <div class="scene-details">
                                        <div class="detail-section transcript-section">
                                            <h4 onclick="toggleDetailContent(this.parentNode.querySelector('.detail-content'))">
                                                <span class="indicator"></span>
                                                Transcript
                                                <span class="toggle-icon">
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                        <path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                    </svg>
                                                </span>
                                            </h4>
                                            <div class="detail-content">${event.transcript}</div>
                                        </div>
                                        
                                        <div class="detail-section prompt-section">
                                            <h4 onclick="toggleDetailContent(this.parentNode.querySelector('.detail-content'))">
                                                <span class="indicator"></span>
                                                Scene Description
                                                <span class="toggle-icon">
                                                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                        <path d="M7 10l5 5 5-5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                                    </svg>
                                                </span>
                                            </h4>
                                            <div class="detail-content">${event.prompt}</div>
                                        </div>
                                    </div>
                                </div>
                            `;
                            
                            sceneCard.innerHTML = imageHtml + contentHtml;
                            eventsContainer.appendChild(sceneCard);
                        }
                    });
                    
                    // Show the session detail view
                    showSessionDetailView();
                })
                .catch(error => {
                    console.error('Error fetching session details:', error);
                    alert('Error loading session details. Please try again.');
                });
        }
        
        function toggleDetailContent(element) {
            element.classList.toggle('expanded');
            const header = element.previousElementSibling;
            header.classList.toggle('expanded');
        }
        
        function openImageModal(src) {
            modalImg.src = src;
            modal.style.display = 'flex';
        }
        
        function showSessionsView() {
            document.getElementById('sessions-view').style.display = 'block';
            document.getElementById('session-detail-view').style.display = 'none';
        }
        
        function showSessionDetailView() {
            document.getElementById('sessions-view').style.display = 'none';
            document.getElementById('session-detail-view').style.display = 'block';
        }
    </script>
</body>
</html> 


<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>D&D Live Scene</title>
  <style>
    :root {
      --bg-primary: #1a1a1a;
      --bg-secondary: #2d2d2d;
      --text-primary: #ffffff;
      --text-secondary: #b3b3b3;
      --accent: #6d28d9;
      --accent-hover: #7c3aed;
      --border: #404040;
      --error: #ef4444;
      --success: #10b981;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body { 
      font-family: 'Segoe UI', system-ui, sans-serif;
      margin: 0;
      padding: 0;
      background-color: var(--bg-primary);
      color: var(--text-primary);
      min-height: 100vh;
    }

    .container {
      max-width: 1600px;
      margin: 0 auto;
      padding: 20px;
    }

    h1 { 
      color: var(--text-primary);
      text-align: center;
      margin: 20px 0;
      font-size: 2.5rem;
      font-weight: 700;
    }

    /* Scene image styles */
    .scene-container {
      width: 100%;
      max-width: 1792px;
      margin: 0 auto;
      background-color: var(--bg-secondary);
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
      position: relative;
      transition: all 0.3s ease;
    }

    .scene-container.fullscreen {
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      max-width: none;
      margin: 0;
      z-index: 1000;
      background-color: rgba(0, 0, 0, 0.9);
      border-radius: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }

    #scene-image {
      width: 100%;
      height: auto;
      display: block;
      transition: opacity 0.3s ease-in-out;
      cursor: pointer;
    }
    
    .scene-container.fullscreen #scene-image {
      max-height: 100vh;
      max-width: 100vw;
      width: auto;
      height: auto;
      object-fit: contain;
    }

    .fullscreen-toggle {
      position: absolute;
      top: 10px;
      right: 10px;
      background-color: rgba(0, 0, 0, 0.5);
      color: white;
      border: none;
      border-radius: 50%;
      width: 40px;
      height: 40px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.2s ease;
      z-index: 1001;
    }

    .fullscreen-toggle:hover {
      background-color: rgba(0, 0, 0, 0.7);
    }

    .fullscreen-toggle svg {
      width: 20px;
      height: 20px;
      fill: currentColor;
    }

    /* Navigation styles */
    .nav-tabs {
      display: flex;
      border-bottom: 1px solid var(--border);
      margin-bottom: 20px;
      background-color: var(--bg-secondary);
      border-radius: 8px 8px 0 0;
      padding: 0 10px;
    }

    .nav-tab {
      padding: 15px 25px;
      cursor: pointer;
      border: 1px solid transparent;
      margin-bottom: -1px;
      color: var(--text-secondary);
      transition: all 0.3s ease;
      border-radius: 8px 8px 0 0;
    }

    .nav-tab:hover {
      color: var(--text-primary);
      background-color: rgba(255, 255, 255, 0.05);
    }

    .nav-tab.active {
      color: var(--text-primary);
      border: 1px solid var(--border);
      border-bottom-color: var(--bg-primary);
      background-color: var(--bg-primary);
    }
    
    /* Character management styles */
    .tab-content {
      display: none;
      padding: 20px;
      background-color: var(--bg-secondary);
      border-radius: 8px;
      margin-top: 20px;
    }

    .tab-content.active { 
      display: block;
    }
    
    .character-form, .environment-form, .style-form {
      margin-bottom: 30px;
      padding: 25px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background-color: var(--bg-primary);
    }

    .character-form h2, .environment-form h2, .style-form h2 {
      margin-bottom: 20px;
      color: var(--text-primary);
    }
    
    .character-form input,
    .character-form textarea,
    .environment-form textarea,
    .style-form input,
    .style-form textarea,
    .style-form select {
      width: 100%;
      margin-bottom: 15px;
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background-color: var(--bg-secondary);
      color: var(--text-primary);
      font-size: 1rem;
    }

    .character-form input:focus,
    .character-form textarea:focus,
    .environment-form textarea:focus,
    .style-form input:focus,
    .style-form textarea:focus,
    .style-form select:focus {
      outline: none;
      border-color: var(--accent);
    }
    
    .character-list {
      display: grid;
      gap: 20px;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    }
    
    .character-card {
      border: 1px solid var(--border);
      padding: 20px;
      border-radius: 8px;
      background-color: var(--bg-primary);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .character-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    .character-card-content h3 {
      color: var(--text-primary);
      margin-bottom: 10px;
    }

    .character-card-content p {
      color: var(--text-secondary);
      margin-bottom: 8px;
      line-height: 1.5;
    }
    
    button {
      padding: 10px 20px;
      margin: 5px;
      border: none;
      border-radius: 6px;
      background-color: var(--accent);
      color: white;
      cursor: pointer;
      font-size: 1rem;
      transition: background-color 0.2s ease;
    }

    button:hover {
      background-color: var(--accent-hover);
    }

    button.delete {
      background-color: var(--error);
    }

    button.delete:hover {
      background-color: #dc2626;
    }
    
    /* Toggle switch styling */
    .toggle-container {
      display: flex;
      align-items: center;
      margin-bottom: 15px;
    }
    
    .toggle-label {
      margin-left: 10px;
      color: var(--text-secondary);
    }
    
    .toggle-switch {
      position: relative;
      display: inline-block;
      width: 52px;
      height: 26px;
    }
    
    .toggle-switch input {
      opacity: 0;
      width: 0;
      height: 0;
    }
    
    .toggle-slider {
      position: absolute;
      cursor: pointer;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-color: var(--bg-secondary);
      transition: .4s;
      border-radius: 34px;
    }
    
    .toggle-slider:before {
      position: absolute;
      content: "";
      height: 18px;
      width: 18px;
      left: 4px;
      bottom: 4px;
      background-color: white;
      transition: .4s;
      border-radius: 50%;
    }
    
    input:checked + .toggle-slider {
      background-color: var(--accent);
    }
    
    input:focus + .toggle-slider {
      box-shadow: 0 0 1px var(--accent);
    }
    
    input:checked + .toggle-slider:before {
      transform: translateX(26px);
    }

    @media (max-width: 768px) {
      .container {
        padding: 10px;
      }

      .nav-tab {
        padding: 10px 15px;
        font-size: 0.9rem;
      }
    }

    /* Scene image styles */
    .scene-prompt-container {
      width: 100%;
      max-width: 1792px;
      margin: 20px auto 0;
      padding: 15px;
      background-color: var(--bg-secondary);
      border-radius: 12px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    .scene-prompt-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    
    .scene-prompt-container h3 {
      color: var(--text-primary);
      font-size: 1.2rem;
      margin: 0;
    }
    
    .clear-button {
      background-color: transparent;
      color: var(--text-secondary);
      border: none;
      border-radius: 50%;
      width: 28px;
      height: 28px;
      padding: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s ease;
    }
    
    .clear-button:hover {
      background-color: rgba(255, 255, 255, 0.1);
      color: var(--error);
    }
    
    .scene-prompt-text {
      color: var(--text-secondary);
      line-height: 1.6;
      font-size: 1rem;
      white-space: pre-wrap;
      max-height: 200px;
      overflow-y: auto;
      padding: 10px;
      background-color: var(--bg-primary);
      border-radius: 6px;
    }

    .sessions-link {
      text-decoration: none;
      margin-left: auto;
    }

    /* Style option grid */
    .style-option-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 15px;
      margin-bottom: 15px;
    }

    .style-option-label {
      display: block;
      margin-bottom: 8px;
      color: var(--text-primary);
      font-weight: 500;
    }

    .style-preview {
      background-color: var(--bg-secondary);
      border-radius: 8px;
      padding: 15px;
      margin-top: 20px;
      border: 1px solid var(--border);
    }

    .style-preview-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }

    .style-preview h3 {
      margin: 0;
      color: var(--text-primary);
    }

    .style-preview-content {
      color: var(--text-secondary);
      white-space: pre-wrap;
      line-height: 1.6;
      font-style: italic;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>D&D Live Scene</h1>
    
    <div class="nav-tabs">
      <div class="nav-tab active" data-tab="scene">Scene</div>
      <div class="nav-tab" data-tab="characters">Characters</div>
      <div class="nav-tab" data-tab="environment">Environment</div>
      <div class="nav-tab" data-tab="style">Style</div>
      <div class="nav-tab" data-tab="audio">Audio</div>
      <a href="{{ sessions_url }}" class="nav-tab sessions-link">Session History</a>
    </div>
    
    <div id="scene-tab" class="tab-content active">
      <div class="scene-container">
        <button class="fullscreen-toggle" onclick="toggleFullscreen()" title="Toggle fullscreen">
          <svg class="expand-icon" viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/>
          </svg>
          <svg class="compress-icon" viewBox="0 0 24 24" width="20" height="20" style="display: none;">
            <path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/>
          </svg>
        </button>
        <img id="scene-image" src="" alt="Generated Scene Image">
      </div>
      
      <div class="scene-prompt-container">
        <div class="scene-prompt-header">
          <h3>Scene Description</h3>
          <button id="clear-scene-prompt" class="clear-button" title="Clear scene context (won't be used in future generations)">
            <svg viewBox="0 0 24 24" width="16" height="16">
              <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
            </svg>
          </button>
        </div>
        <div id="scene-prompt-text" class="scene-prompt-text">
          No scene has been generated yet.
        </div>
      </div>
    </div>
    
    <div id="environment-tab" class="tab-content">
      <div class="environment-form">
        <h2>Environment Settings</h2>
        <div class="toggle-container">
          <label class="toggle-switch">
            <input type="checkbox" id="environment-lock">
            <span class="toggle-slider"></span>
          </label>
          <span class="toggle-label">Lock environment (prevent automatic updates)</span>
        </div>
        <textarea id="environment-description" placeholder="Environment Description" rows="6"></textarea>
        <button onclick="saveEnvironment()">Save Environment</button>
      </div>
      
      <div class="environment-info">
        <h3>About Environment Settings</h3>
        <p>
          The environment description provides context for scene generation. It's automatically updated based 
          on session transcripts, but you can manually edit it or lock it to prevent changes.
        </p>
        <p>
          Keep descriptions concise and focused on visual elements like location, time of day, 
          weather, and general atmosphere.
        </p>
      </div>
    </div>
    
    <div id="characters-tab" class="tab-content">
      <div class="character-form">
        <h2>Add/Update Character</h2>
        <input type="text" id="character-id" placeholder="Character ID (e.g., wizard_001)">
        <input type="text" id="character-name" placeholder="Character Name">
        <textarea id="character-description" placeholder="Character Description" rows="4"></textarea>
        <button onclick="saveCharacter()">Save Character</button>
      </div>
      
      <h2>Characters</h2>
      <div id="character-list" class="character-list">
        <!-- Characters will be populated here -->
      </div>
    </div>

    <div id="style-tab" class="tab-content">
      <div class="style-form">
        <h2>Global Image Style</h2>
        <p class="style-description">
          This style directive is added to every scene prompt to guide the AI image generator.
          It helps maintain a consistent visual style across your adventure.
        </p>
        
        <label class="style-option-label">Style Directive</label>
        <textarea id="style-text" placeholder="Enter your style directive..." rows="6"></textarea>
        
        <button id="save-style">Save Style</button>
        <button id="reset-style">Reset to Default</button>
        
        <div class="style-info">
          <h3>Tips for Effective Style Directives</h3>
          <p>
            Effective style directives should include:
            <ul style="margin-left: 20px; margin-top: 10px; line-height: 1.4">
              <li><strong>Art style:</strong> e.g., "oil painting", "anime", "photorealistic", "watercolor", etc.</li>
              <li><strong>Color palette:</strong> e.g., "vibrant", "muted earth tones", "dark and moody", etc.</li>
              <li><strong>Lighting:</strong> e.g., "dramatic lighting", "soft diffused light", "golden hour", etc.</li>
              <li><strong>Composition:</strong> e.g., "cinematic", "balanced", "wide-angle view", etc.</li>
              <li><strong>Detail level:</strong> e.g., "highly detailed", "simplified", "textured", etc.</li>
            </ul>
          </p>
          <p style="margin-top: 15px">
            <em>Example:</em> "Art style: fantasy oil painting. Color palette: vibrant and rich. Lighting: dramatic with strong shadows. Composition: balanced and cinematic. Level of detail: high with carefully rendered textures."
          </p>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Include Socket.IO client library -->
  <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
  <!-- Custom client script -->
  <script src="{{ url_for('static', filename='js/client.js') }}"></script>
</body>
</html>


document.addEventListener("DOMContentLoaded", function () {
    // Establish a connection to the server using Socket.IO.
    var socket = io();
  
    socket.on('connect', function() {
      console.log("Connected to server via Socket.IO");
      // Load characters and environment when connected
      loadCharacters();
      loadEnvironment();
      loadScenePrompt();
      loadStyle();
    });
  
    // Listen for new image updates from the server
    socket.on('new_image', function(data) {
      console.log("Received new image update:", data);
      if (data && data.image_url) {
        updateSceneImage(data.image_url);
      } else {
        console.error("Received invalid image data:", data);
      }
    });
    
    // Listen for environment updates from the server
    socket.on('environment_update', function(data) {
      console.log("Received environment update:", data);
      if (data && data.description) {
        // Update the environment description in the UI
        const descriptionElement = document.getElementById('environment-description');
        if (descriptionElement) {
          descriptionElement.value = data.description;
        }
      } else {
        console.error("Received invalid environment data:", data);
      }
    });
    
    // Listen for scene prompt updates from the server
    socket.on('scene_prompt_update', function(data) {
      console.log("Received scene prompt update:", data);
      if (data && data.prompt !== undefined) {
        // Update the scene prompt in the UI
        updateScenePrompt(data.prompt);
      } else {
        console.error("Received invalid scene prompt data:", data);
      }
    });
    
    // Listen for style updates from the server
    socket.on('style_update', function(data) {
      console.log("Received style update:", data);
      if (data && data.style_data) {
        displayStyle(data.style_data);
      } else {
        console.error("Received invalid style data:", data);
      }
    });
    
    // Set up clear scene prompt button
    const clearScenePromptButton = document.getElementById('clear-scene-prompt');
    if (clearScenePromptButton) {
      clearScenePromptButton.addEventListener('click', clearScenePrompt);
    }
    
    // Set up style form functionality
    initStyleForms();

    // Add keyboard event listener for fullscreen toggle
    document.addEventListener('keydown', function(e) {
      // Toggle fullscreen on 'F' key or Escape
      if (e.key === 'f' || e.key === 'F') {
        toggleFullscreen();
      } else if (e.key === 'Escape') {
        const container = document.querySelector('.scene-container');
        if (container.classList.contains('fullscreen')) {
          toggleFullscreen();
        }
      }
    });
  
    function updateSceneImage(imageUrl) {
      var imageElement = document.getElementById("scene-image");
      if (imageElement) {
        console.log("Updating scene image with:", imageUrl);
        // First set opacity to 0 for fade effect
        imageElement.style.opacity = 0;
        
        // Create a new image object to preload
        var img = new Image();
        img.onload = function() {
          // Once loaded, update the src and fade in
          imageElement.src = imageUrl;
          setTimeout(() => {
            imageElement.style.opacity = 1;
          }, 50);
        };
        img.onerror = function() {
          console.error("Failed to load image:", imageUrl);
        };
        img.src = imageUrl;
      } else {
        console.error("Scene image element not found");
      }
    }
    
    function updateScenePrompt(promptText) {
      const promptElement = document.getElementById('scene-prompt-text');
      if (promptElement) {
        promptElement.textContent = promptText || "No scene has been generated yet.";
      }
    }
  
    async function clearScenePrompt() {
      try {
        const response = await fetch('/scene_prompt', {
          method: 'DELETE'
        });
        
        if (response.ok) {
          console.log('Scene prompt cleared successfully');
        } else {
          console.error('Error clearing scene prompt');
        }
      } catch (error) {
        console.error('Error clearing scene prompt:', error);
      }
    }
  
    // Optional: fallback mechanism to refresh periodically
    // setInterval(function(){
    //   location.reload();
    // }, 60000); // refresh page every 60 seconds if needed

    // Tab switching functionality
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        // Remove active class from all tabs and contents
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked tab and corresponding content
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab + '-tab').classList.add('active');
      });
    });
});

// Scene Prompt Management Functions
async function loadScenePrompt() {
    try {
        const response = await fetch('/scene_prompt');
        const data = await response.json();
        if (data.prompt) {
            updateScenePrompt(data.prompt);
        }
    } catch (error) {
        console.error('Error loading scene prompt:', error);
    }
}

function updateScenePrompt(promptText) {
    const promptElement = document.getElementById('scene-prompt-text');
    if (promptElement) {
        promptElement.textContent = promptText || "No scene has been generated yet.";
    }
}

// Environment Management Functions
async function loadEnvironment() {
    try {
        const response = await fetch('/environment');
        const environment = await response.json();
        displayEnvironment(environment);
    } catch (error) {
        console.error('Error loading environment:', error);
    }
}

function displayEnvironment(environment) {
    const descriptionElement = document.getElementById('environment-description');
    const lockElement = document.getElementById('environment-lock');
    
    if (descriptionElement) {
        descriptionElement.value = environment.description || '';
    }
    
    if (lockElement) {
        lockElement.checked = environment.locked || false;
    }
}

async function saveEnvironment() {
    const description = document.getElementById('environment-description').value;
    const locked = document.getElementById('environment-lock').checked;
    
    if (!description) {
        alert('Please provide an environment description');
        return;
    }
    
    try {
        const response = await fetch('/environment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                description: description,
                locked: locked
            })
        });
        
        if (response.ok) {
            const updatedEnvironment = await response.json();
            displayEnvironment(updatedEnvironment);
            alert('Environment settings saved successfully');
        } else {
            alert('Error saving environment settings');
        }
    } catch (error) {
        console.error('Error saving environment:', error);
        alert('Error saving environment settings');
    }
}

// Character Management Functions
async function loadCharacters() {
    try {
        const response = await fetch('/characters');
        const characters = await response.json();
        displayCharacters(characters);
    } catch (error) {
        console.error('Error loading characters:', error);
    }
}

function displayCharacters(characters) {
    const characterList = document.getElementById('character-list');
    characterList.innerHTML = '';
    
    for (const [id, data] of Object.entries(characters)) {
        const card = document.createElement('div');
        card.className = 'character-card';
        card.innerHTML = `
            <div class="character-card-content">
                <h3>${data.name || id}</h3>
                <p><strong>ID:</strong> ${id}</p>
                <p>${data.description || 'No description provided.'}</p>
                <button onclick="editCharacter('${id}')">Edit</button>
                <button class="delete" onclick="deleteCharacter('${id}')">Delete</button>
            </div>
        `;
        characterList.appendChild(card);
    }
}

function editCharacter(id) {
    fetch(`/characters/${id}`)
        .then(response => response.json())
        .then(character => {
            document.getElementById('character-id').value = id;
            document.getElementById('character-name').value = character.name || '';
            document.getElementById('character-description').value = character.description || '';
        })
        .catch(error => console.error('Error loading character:', error));
}

async function saveCharacter() {
    const id = document.getElementById('character-id').value;
    const name = document.getElementById('character-name').value;
    const description = document.getElementById('character-description').value;
    
    if (!id || !name || !description) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                description: description
            })
        });
        
        if (response.ok) {
            loadCharacters();
            // Clear form
            document.getElementById('character-id').value = '';
            document.getElementById('character-name').value = '';
            document.getElementById('character-description').value = '';
        } else {
            alert('Error saving character');
        }
    } catch (error) {
        console.error('Error saving character:', error);
        alert('Error saving character');
    }
}

async function deleteCharacter(id) {
    if (!confirm(`Are you sure you want to delete character ${id}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/characters/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadCharacters();
        } else {
            alert('Error deleting character');
        }
    } catch (error) {
        console.error('Error deleting character:', error);
        alert('Error deleting character');
    }
}

// Add the toggleFullscreen function
function toggleFullscreen() {
  const container = document.querySelector('.scene-container');
  const expandIcon = container.querySelector('.expand-icon');
  const compressIcon = container.querySelector('.compress-icon');
  
  container.classList.toggle('fullscreen');
  
  // Toggle icon visibility
  expandIcon.style.display = container.classList.contains('fullscreen') ? 'none' : 'block';
  compressIcon.style.display = container.classList.contains('fullscreen') ? 'block' : 'none';
  
  // Prevent scrolling when in fullscreen
  document.body.style.overflow = container.classList.contains('fullscreen') ? 'hidden' : '';
}

// Make toggleFullscreen available globally
window.toggleFullscreen = toggleFullscreen;

// Make environment functions available globally
window.saveEnvironment = saveEnvironment;

// Style Management Functions
async function loadStyle() {
    try {
        const response = await fetch('/style');
        const styleData = await response.json();
        displayStyle(styleData);
    } catch (error) {
        console.error('Error loading style settings:', error);
    }
}

function displayStyle(styleData) {
    // Update style text field with data from server
    if (!styleData) return;

    const styleTextField = document.getElementById('style-text');
    if (styleTextField && styleData.style_text) {
        styleTextField.value = styleData.style_text;
    }
}

async function saveStyle() {
    // Get value from the style text field
    const styleText = document.getElementById('style-text').value;
    
    if (!styleText) {
        alert('Please provide a style directive');
        return;
    }
    
    try {
        const response = await fetch('/style', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                style_text: styleText
            })
        });
        
        if (response.ok) {
            console.log('Style saved successfully');
            // The server will emit a style_update event that will update the UI
        } else {
            console.error('Error saving style');
            alert('Error saving style');
        }
    } catch (error) {
        console.error('Error saving style:', error);
        alert('Error saving style');
    }
}

async function resetStyle() {
    try {
        const response = await fetch('/style/reset', {
            method: 'POST'
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Style reset successfully');
            // Update the UI with the reset values
            displayStyle(data.style_data);
        } else {
            console.error('Error resetting style');
            alert('Error resetting style');
        }
    } catch (error) {
        console.error('Error resetting style:', error);
        alert('Error resetting style');
    }
}

function initStyleForms() {
    // Add event listeners for the style form buttons
    document.getElementById('save-style')?.addEventListener('click', saveStyle);
    document.getElementById('reset-style')?.addEventListener('click', resetStyle);
}

// Make style functions available globally
window.saveStyle = saveStyle;
window.resetStyle = resetStyle;
  


















