# whisper_asr.py

import whisper


class WhisperASR:
    def __init__(self, model_path="base"):
        """
        Initialize the Whisper ASR model.
        """
        self.model = whisper.load_model(model_path)

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe the provided audio file using the Whisper ASR model.

        Parameters:
        - audio_file_path: Path to the audio file to be transcribed.

        Returns:
        - Transcribed text as a string.
        """
        result = self.model.transcribe(audio_file_path)
        return result["text"]

    def detailed_transcription(self, audio_file_path: str) -> dict:
        """
        Transcribe the provided audio file with detailed information
        including detected language.

        Parameters:
        - audio_file_path: Path to the audio file to be transcribed.

        Returns:
        - Dictionary containing transcribed text and detected language.
        """
        # Load and preprocess the audio
        audio = whisper.load_audio(audio_file_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(self.model.device)

        # Detect language
        _, probs = self.model.detect_language(mel)
        detected_language = max(probs, key=probs.get)

        # Decode audio to text
        options = whisper.DecodingOptions()
        result = whisper.decode(self.model, mel, options)

        return {
            "text": result.text,
            "language": detected_language
        }


if __name__ == "__main__":
    # Test the Whisper ASR functionality
    asr = WhisperASR()
    audio_file = "sample_audio.mp3"

    print("Simple transcription:")
    print(asr.transcribe(audio_file))

    print("\nDetailed transcription:")
    print(asr.detailed_transcription(audio_file))
