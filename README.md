# D&D Live Scene Generator

This project provides a real-time pipeline to capture live audio from a Dungeons & Dragons session, transcribe it using a local Whisper model, generate a detailed scene description via OpenAI GPT, and create a corresponding image using DALL-E 3. The generated image is pushed to a live web dashboard for immediate viewing.

## Project Structure

```
project/
├── client/
│   └── recorder.py         # Captures audio from your laptop and sends chunks to the server.
├── server/
│   ├── app.py              # Main Flask & Socket.IO application.
│   ├── config.py           # Central configuration settings.
│   ├── transcribe.py       # Transcribes audio using the local Whisper model.
│   ├── scene_composer.py   # Generates a scene description from the transcript and character data.
│   ├── image_generator.py  # Calls the OpenAI image API (DALL-E 3) to generate images.
│   ├── character_store.py  # File-based character database (JSON).
│   ├── audio_processor.py  # (Optional) Audio processing for incoming chunks.
│   ├── templates/
│   │   └── index.html      # Web dashboard template.
│   └── static/
│       └── js/
│           └── client.js   # Client-side JS for live image updates via Socket.IO.
├── requirements.txt        # Python dependencies.
└── README.md               # This file.
```

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/dd-live-scene.git
   cd dd-live-scene
   ```

2. **Create a Virtual Environment and Install Dependencies:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Additional Dependencies:**

   - For audio recording on the client:
     ```bash
     pip install sounddevice soundfile numpy requests
     ```
   - For transcription with Whisper:
     ```bash
     pip install git+https://github.com/openai/whisper.git
     ```

## Configuration

Copy the `.env.example` file to `.env` and update the following environment variables as needed:

### API Keys
- `OPENAI_API_KEY`: Your OpenAI API key for GPT and DALL-E services

### Flask Configuration
- `SECRET_KEY`: Flask secret key for session security (change in production)
- `FLASK_ENV`: Set to 'development' or 'production'
- `DEBUG`: Set to 'True' for development, 'False' for production

### Audio Recording Settings
- `CHUNK_DURATION`: Duration of each audio chunk in seconds (default: 60)
- `SAMPLE_RATE`: Audio sample rate in Hz (default: 44100)
- `CHANNELS`: Number of audio channels (default: 1)

### Data Storage
- `CHARACTER_DATA_PATH`: Path to store character data (default: server/character_data)

All these settings can also be modified directly in `server/config.py` if preferred.

## Running the Application

1. **Start the Server:**

   In the `server/` directory, run:

   ```bash
   python app.py
   ```

   The server will be accessible at [http://localhost:5000](http://localhost:5000).

2. **Run the Recorder Client:**

   On your laptop, from the `client/` directory, run:

   ```bash
   python recorder.py
   ```

   This will capture live audio, segment it into chunks, and send each chunk to the server.

3. **View the Live Dashboard:**

   Open a web browser and navigate to [http://localhost:5000](http://localhost:5000) to see the generated scene images update in real time.

## License

This project is licensed under the MIT License.
