# audio_capture.py

import pyaudio
import wave
import os
import tempfile

# Import the configuration from settings.py
from config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS, AUDIO_FORMAT


class AudioCapture:
    def __init__(self):
        self.audio = pyaudio.PyAudio()

        self.chunk_size = 1024
        self.format = pyaudio.paInt16  # Suitable format for most microphones

    def capture_audio(self, duration: int) -> str:
        """
        Capture audio for a specified duration in seconds.

        Returns:
            str: Path to the temporary file where the audio is saved.
        """

        # Create a stream for audio capture
        stream = self.audio.open(format=self.format, channels=AUDIO_CHANNELS,
                                 rate=AUDIO_SAMPLE_RATE, input=True,
                                 frames_per_buffer=self.chunk_size)

        print("Recording...")

        frames = []

        # Capture audio in chunks and append to frames
        for _ in range(0, int(AUDIO_SAMPLE_RATE / self.chunk_size * duration)):
            data = stream.read(self.chunk_size)
            frames.append(data)

        print("Recording finished.")

        # Stop and close the audio stream
        stream.stop_stream()
        stream.close()

        # Use a temporary file to store the audio
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{AUDIO_FORMAT}")
        file_path = temp_file.name

        # Save audio data to the temporary file in WAV format
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(AUDIO_CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(AUDIO_SAMPLE_RATE)
            wf.writeframes(b''.join(frames))

        return file_path

    def close(self):
        """
        Properly terminate the audio interface.
        """
        self.audio.terminate()


if __name__ == "__main__":
    # Test the audio capture for 5 seconds if run directly
    capturer = AudioCapture()
    output_file = capturer.capture_audio(5)
    print(f"Saved recording to {output_file}")
    capturer.close()
