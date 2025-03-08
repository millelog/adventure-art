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