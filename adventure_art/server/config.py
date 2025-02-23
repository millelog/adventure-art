"""
config.py

Central configuration settings for the server.
Override any default values by setting environment variables.
"""

import os
import sys
from pathlib import Path

# Audio settings
CHUNK_DURATION = int(os.environ.get('CHUNK_DURATION', 60))  # seconds per audio chunk
SAMPLE_RATE = int(os.environ.get('SAMPLE_RATE', 44100))
CHANNELS = int(os.environ.get('CHANNELS', 1))

# API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable is not set!")
    print("Please check that:")
    print("1. Your .env file exists in the project root directory")
    print("2. It contains a valid OPENAI_API_KEY")
    print("3. The application has permission to read the file")
    sys.exit(1)

# Get project root directory
project_root = Path(__file__).resolve().parent.parent.parent

# File-based character store configuration
CHARACTER_DATA_PATH = os.environ.get('CHARACTER_DATA_PATH', 
    str(project_root / 'adventure_art' / 'server' / 'character_data'))

# Flask and SocketIO configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')  # Make sure to change in production
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
