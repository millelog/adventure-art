#!/usr/bin/env python3
"""
app.py

Main server application that:
- Serves the live display frontend.
- Receives audio chunks via the /upload_audio endpoint.
- Processes audio: transcription → scene composition → image generation.
- Pushes the newly generated image to connected clients using SocketIO.
"""

import os
from flask import Flask, request, render_template
from flask_socketio import SocketIO
import traceback

# Import downstream processing modules.
# These modules should implement the following functions:
# - transcribe.transcribe_audio(audio_file)
# - scene_composer.compose_scene(transcript)
# - image_generator.generate_image(scene_description)
import transcribe
import scene_composer
import image_generator

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Update this for production.
socketio = SocketIO(app)

@app.route('/')
def index():
    """Render the main display page."""
    return render_template('index.html')


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
