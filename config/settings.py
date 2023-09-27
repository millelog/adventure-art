# settings.py

import os

# ===== API Configuration =====
OPENAI_API_KEY = os.environ.get('ADVENTURE_ART_OPENAI_API_KEY', '')

# ===== Audio Configuration =====
AUDIO_SAMPLE_RATE = 44100
AUDIO_CHANNELS = 2  # Stereo
AUDIO_FORMAT = 'wav'  # Default audio format

# ===== File Paths & Directories =====
LOG_DIR = 'logs/'
ASSET_DIR = 'gui/assets/'

# ===== GUI Configuration =====
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
DEFAULT_FONT = 'Arial 12'

# ===== Environment Settings =====
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
DEBUG = True if ENVIRONMENT == 'development' else False

# ===== Rate Limits & Quotas =====
WHISPER_RATE_LIMIT = 1000  # Example value, requests per hour
OPENAI_RATE_LIMIT = 2000  # Example value, requests per hour

# ===== Database (if applicable) =====
DATABASE_URI = os.environ.get('DATABASE_URI', 'default_db_connection_string')

# ===== Additional Constants or Configuration =====
DEFAULT_PROMPT_LENGTH = 200
