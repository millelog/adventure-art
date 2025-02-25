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
