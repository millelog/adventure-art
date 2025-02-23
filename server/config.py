"""
config.py

Central configuration settings for the server.
Override any default values by setting environment variables.
"""

import os

# Audio settings
CHUNK_DURATION = int(os.environ.get('CHUNK_DURATION', 60))  # seconds per audio chunk
SAMPLE_RATE = int(os.environ.get('SAMPLE_RATE', 44100))
CHANNELS = int(os.environ.get('CHANNELS', 1))

# API Keys (replace default placeholder strings or set via environment)
WHISPER_API_KEY = os.environ.get('WHISPER_API_KEY', 'your_whisper_api_key')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'your_openai_api_key')
DALLE_API_KEY = os.environ.get('DALLE_API_KEY', 'your_dalle_api_key')

# API Endpoints (placeholders; update as necessary)
WHISPER_API_URL = os.environ.get('WHISPER_API_URL', 'https://api.whisper.ai/v1/transcribe')
OPENAI_GPT_URL = os.environ.get('OPENAI_GPT_URL', 'https://api.openai.com/v1/completions')
DALLE_API_URL = os.environ.get('DALLE_API_URL', 'https://api.openai.com/v1/images/generations')

# File-based character store configuration
# This is the directory where character descriptions and reference images are stored.
CHARACTER_DATA_PATH = os.environ.get('CHARACTER_DATA_PATH', os.path.join(os.getcwd(), 'server', 'character_data'))

# Flask and SocketIO configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

# Other configurable parameters (if needed)
DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')
