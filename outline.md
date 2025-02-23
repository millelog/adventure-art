Below is a detailed blueprint of the Python files (and supporting files) you’ll need for the project. This document outlines the file structure, where each file should live, its purpose, and the context required so that each module’s content can be generated accurately. We’re keeping things simple by using a file‐based system for character descriptions and reference images and omitting any seed‐based techniques. The system is split into a client (running on your laptop to capture and send audio) and a server (handling transcription, scene composition, image generation, and live frontend updates).

---

## Project Structure

```
project/
├── client/
│   └── recorder.py
├── server/
│   ├── app.py
│   ├── config.py
│   ├── transcribe.py
│   ├── scene_composer.py
│   ├── image_generator.py
│   ├── character_store.py
│   ├── audio_processor.py
│   ├── templates/
│   │   └── index.html
│   └── static/
│       └── js/
│           └── client.js
├── requirements.txt
└── README.md
```

---

## File Descriptions & Context

### 1. Client Files

#### **client/recorder.py**
- **Purpose:**  
  - Captures live audio from your laptop’s microphone.
  - Splits the continuous audio into configurable time windows (e.g., every 60 seconds).
  - Sends each audio chunk to the server via an HTTP endpoint (or via websockets, if preferred).

- **Key Context:**  
  - Use a library such as [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) or [sounddevice](https://python-sounddevice.readthedocs.io/) to capture audio.
  - Implement a simple timer or loop to segment audio.
  - Package the audio chunk (as a file or binary blob) and send it using the Python `requests` library (or a websocket client library if you choose that route).
  - Include error handling and reconnection logic for network issues.

---

### 2. Server Files

#### **server/app.py**
- **Purpose:**  
  - Acts as the main Flask application that orchestrates the entire pipeline.
  - Receives audio chunks from the client, triggers the downstream processing (transcription, scene description, and image generation), and then updates the frontend display.
  - Uses Flask-SocketIO (or a similar mechanism) to push new image updates to connected web clients.

- **Key Context:**  
  - Set up API endpoints (e.g., `/upload_audio`) to receive audio chunks.
  - Import and coordinate functions from `transcribe.py`, `scene_composer.py`, `image_generator.py`, `character_store.py`, and `audio_processor.py`.
  - Manage session state and error handling.
  - Serve the frontend (via templates and static files) to display the generated image.

---

#### **server/config.py**
- **Purpose:**  
  - Centralizes configuration settings for the project.
  - Stores API keys (for Whisper, OpenAI GPT, and DALL-E), file paths, time window lengths, and other adjustable parameters.

- **Key Context:**  
  - Use environment variables for sensitive data.
  - Define constants such as the audio window duration, API endpoints, and file paths for character storage.

---

#### **server/transcribe.py**
- **Purpose:**  
  - Contains functions that send an audio chunk to the Whisper API and return the transcribed text.

- **Key Context:**  
  - Accepts an audio file or binary data.
  - Uses the `requests` library (or an appropriate client) to interact with the Whisper API.
  - Implements retry logic and error handling if the API call fails.

---

#### **server/scene_composer.py**
- **Purpose:**  
  - Takes the transcript from the audio and retrieves character details from the file-based store.
  - Calls an OpenAI GPT model to generate a detailed scene description, ensuring the main characters are described consistently.

- **Key Context:**  
  - Combine dynamic transcript data with static character information (from `character_store.py`).
  - Format the prompt appropriately for GPT.
  - Return a narrative scene description that will be used by the image generation module.

---

#### **server/image_generator.py**
- **Purpose:**  
  - Receives the scene description and calls the DALL-E 3 API to generate an image of the scene.
  - Returns the URL or image data for the generated image.

- **Key Context:**  
  - Construct a detailed prompt from the scene description.
  - Use the OpenAI API to invoke DALL-E without using any seed numbers or extra seed consistency methods.
  - Handle API responses and errors.

---

#### **server/character_store.py**
- **Purpose:**  
  - Implements a file-based storage system for character descriptions and reference images.
  - Provides functions to load, update, and retrieve character data.

- **Key Context:**  
  - Use JSON files and/or structured directories to store character information.
  - Offer simple read/write operations to keep character data current.
  - This module allows the scene composer to include consistent character details in its prompts.

---

#### **server/audio_processor.py**
- **Purpose:**  
  - Handles buffering and slicing of incoming audio data from the client.
  - Triggers the transcription process once a complete time window (e.g., 60 seconds) has been collected.

- **Key Context:**  
  - Accumulate audio data into defined chunks.
  - Call the transcription function once each window is complete.
  - May use lightweight libraries for simple audio manipulation if needed.

---

### 3. Frontend Files

#### **server/templates/index.html**
- **Purpose:**  
  - Provides the simple web dashboard that displays the latest generated image.
  - Contains an `<img>` tag to show the image and includes JavaScript for auto-updating.

- **Key Context:**  
  - Basic HTML layout that integrates with Flask’s templating engine.
  - Include necessary references to static JS files (e.g., `client.js`) to handle live updates.
  - The page should be simple, focusing on displaying the updated image as soon as it’s available.

---

#### **server/static/js/client.js**
- **Purpose:**  
  - Contains JavaScript that connects to the server (via SocketIO or similar) to listen for update events.
  - Updates the image on the page automatically when a new image is generated.

- **Key Context:**  
  - Use the Socket.IO client library to establish a connection with the Flask-SocketIO endpoint.
  - Listen for a custom event (such as `new_image`) that carries the URL or data of the newly generated image.
  - On receiving the update, change the `<img>` element’s `src` attribute to display the new image.
  - Optionally implement fallback logic (e.g., periodic refresh) if using websockets is not feasible.

---

### 4. Additional Files

#### **requirements.txt**
- **Purpose:**  
  - Lists all Python dependencies for the project.

- **Key Context:**  
  - Include packages such as:
    - Flask
    - Flask-SocketIO
    - openai
    - requests
    - PyAudio or sounddevice  
  - This file is used to set up your virtual environment quickly.

#### **README.md**
- **Purpose:**  
  - Provides an overview of the project, installation instructions, configuration details, and usage guidelines.
  
- **Key Context:**  
  - Document the project architecture and file structure.
  - Explain how to set up and run both the client and server.
  - Include instructions on configuring API keys and any required environment variables.

---

## Summary

This blueprint breaks down the project into a set of clearly defined Python modules and supporting files:

- The **client** captures and sends audio.
- The **server** (using Flask and Flask-SocketIO) handles audio processing, transcription via Whisper, scene description via GPT, image generation via DALL-E, and finally pushes real-time updates to the frontend.
- A file-based character store ensures that main PC details are consistently included in each scene.
- A minimalistic **frontend** displays the generated image with real-time updates using websockets (or a periodic refresh strategy).

Each module is designed with simplicity in mind while ensuring all components (audio capture, processing, and live display) integrate seamlessly. This document should provide all the context needed to generate the content for each file accurately.