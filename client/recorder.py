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
CHUNK_DURATION = 60       # Duration of each audio chunk in seconds
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
