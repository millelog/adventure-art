# D&D Live Scene Generator

This project provides a real-time pipeline to capture live audio from a Dungeons & Dragons session, transcribe it using a local Whisper model, generate a detailed scene description via OpenAI GPT-4o, and create a corresponding image using Google's Imagen 3.0 API. The generated image is pushed to a live web dashboard for immediate viewing.

![Live Scene View](assets/preview.png)
*Live scene generation with fullscreen toggle and real-time updates*

![Character Management](assets/preview2.png)
*Character management interface for maintaining consistent descriptions*

![Session History](assets/preview3.png)
*Session history view with downloadable transcripts and scene descriptions*

![Environment Management](assets/preview4.png)
*Environment management interface for tracking and updating game settings*

## Features

- **Live Audio Processing**: Captures and processes audio in real-time from your D&D session
- **Smart Scene Generation**: Uses GPT-4o to identify key moments and create vivid scene descriptions
- **Character Consistency**: Maintains character descriptions across generated scenes
- **Scene Continuity**: Maintains visual consistency between consecutive scenes by considering previous scene descriptions
- **Environment Management**: Automatically tracks and updates the game environment based on session context
- **Environment Locking**: Option to lock environment descriptions to prevent automatic updates
- **Real-time Updates**: Instantly displays generated images via Socket.IO
- **Fullscreen Mode**: Toggle fullscreen view with 'F' key or button
- **Character Management**: Simple interface to add, edit, and delete character descriptions
- **Scene Context Reset**: Option to clear previous scene context when needed
- **Session History**: Archive and browse past sessions with downloadable transcripts and scene descriptions

## Project Structure

```
project/
├── client/
│   └── recorder.py        # Captures audio from your laptop and sends chunks to the server
├── adventure_art/server/
│   ├── app.py             # Main Flask & Socket.IO application
│   ├── config.py          # Central configuration settings
│   ├── transcribe.py      # Transcribes audio using the local Whisper model
│   ├── scene_composer.py  # Generates scene descriptions using GPT-4o
│   ├── image_generator.py # Generates images using Google's Imagen 3.0
│   ├── character_store.py # File-based character database (JSON)
│   ├── environment_store.py # File-based environment state management
│   ├── environment_analyzer.py # Analyzes transcripts for environment changes
│   ├── image_cache.py     # Manages caching of generated images
│   ├── session_history.py # Records and manages session history data
│   ├── templates/
│   │   ├── index.html     # Web dashboard template
│   │   └── sessions.html  # Session history viewer template
│   └── static/
│       └── js/
│           └── client.js  # Client-side JS for live updates
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/millelog/adventure-art.git
   cd adventure-art
   ```

2. **Create a Virtual Environment and Install Dependencies:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
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

Copy the `.env.example` file to `.env` and update the following environment variables:

### API Keys
- `OPENAI_API_KEY`: Your OpenAI API key for GPT-4o
- `GEMINI_API_KEY`: Your Google API key for Imagen 3.0

### Flask Configuration
- `SECRET_KEY`: Flask secret key for session security (change in production)
- `FLASK_ENV`: Set to 'development' or 'production'
- `DEBUG`: Set to 'True' for development, 'False' for production

### Data Storage
- `CHARACTER_DATA_PATH`: Path to store character data and cached images
- `ENVIRONMENT_DATA_PATH`: Path to store environment state data (defaults to CHARACTER_DATA_PATH)

All these settings can also be modified directly in `server/config.py` if preferred.

### Recording Settings

To change the recording settings, modify the following variables in `client/recorder.py`:

- `CHUNK_DURATION`: Duration of each audio chunk in seconds (default: 120)
- `SAMPLE_RATE`: Audio sample rate in Hz (default: 44100)
- `CHANNELS`: Number of audio channels (default: 1)

## Usage

1. **Start the Server:**

   ```bash
   python server/app.py
   ```

   The web interface will be accessible at [http://localhost:5000](http://localhost:5000)

2. **Run the Recorder Client:**

   ```bash
   python client/recorder.py
   ```

3. **Manage Characters:**
   - Navigate to the "Character Management" tab
   - Add characters with unique IDs, names, and descriptions
   - These descriptions will be used to maintain consistency in generated scenes

4. **Manage Environment:**
   - Navigate to the "Environment" tab
   - View and edit the current environment description
   - Toggle the lock switch to prevent automatic updates
   - Environment descriptions focus on location, atmosphere, time of day, and weather

5. **View Generated Scenes:**
   - The main tab shows the latest generated scene
   - Press 'F' or click the fullscreen button to toggle fullscreen mode
   - Press 'ESC' to exit fullscreen

## How It Works

1. The recorder captures audio in 60-second chunks
2. Each chunk is transcribed using Whisper
3. The transcript is analyzed for significant environment changes
4. If unlocked, the environment description is updated based on the analysis
5. GPT-4o analyzes the transcript, character descriptions, current environment, and previous scene to identify key moments
6. A detailed scene description is generated, maintaining character and environment consistency
7. The scene description is stored for future reference to maintain continuity
8. Google's Imagen 3.0 creates an image based on the description
9. The image and scene description are displayed in real-time on the web dashboard

### Environment Management

The environment system maintains a persistent description of the game's current setting. This description is:

- **Automatically Updated**: The system analyzes each audio transcript for significant location or setting changes
- **Conservative**: Only updates when there's clear evidence of a meaningful change
- **Lockable**: Can be locked to prevent automatic updates during important scenes
- **Manually Editable**: Users can directly edit the description through the UI
- **Context-Aware**: Provides consistent context for scene generation
- **Focused on Visuals**: Emphasizes elements that would appear in an image (location, lighting, weather, etc.)

### Scene Continuity

The scene continuity system helps maintain visual consistency between consecutive scene generations:

- **Previous Scene Context**: Each generated scene description is stored and used as context for the next generation
- **Adaptive Continuity**: The system maintains visual consistency while still focusing on new actions or moments
- **Context Reset**: Users can clear the previous scene context via the UI if they want to start fresh
- **Real-time Updates**: Scene descriptions are displayed below the generated image and update in real-time
- **Bidirectional Influence**: Previous scenes influence both environment analysis and scene composition

This approach creates a more coherent visual narrative throughout your D&D session, even as the action and focus change.

### Session History

The session history system automatically records and organizes your D&D sessions:

- **Automatic Session Tracking**: The system creates a new session when the server starts or when needed
- **Scene Archiving**: Each generated scene is saved with its transcript, description, and image
- **Browsable History**: Access past sessions through the Session History interface
- **Downloadable Content**: Download all transcripts or scene descriptions from a session as text files
- **Chronological Organization**: Sessions and scenes are organized by date and time
- **Image Viewer**: View full-size scene images with a click
- **Expandable Details**: Toggle between compact and expanded views of transcripts and scene descriptions

To access session history:
1. Navigate to the "Session History" tab in the web interface
2. Browse through past sessions
3. Click on a session to view all scenes from that session
4. Use the download buttons to save transcripts or scene descriptions as text files
5. Click on any image to view it in full size

This feature helps you maintain a record of your campaign's key moments and provides valuable reference material for future sessions.

## License

This project is licensed under the MIT License.
