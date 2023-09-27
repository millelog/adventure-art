import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from input.audio_capture import AudioCapture
from asr.whisper_asr import WhisperASR
from api_parser.openai_parser import OpenAIParser
# Import the image generation and GUI modules when they are available
# from image_generator.text_to_image import TextToImage
# from gui.display import Display

def main():
    # 1. Capture audio
    capturer = AudioCapture()
    audio_file_path = capturer.capture_audio(30)  # Capture for 5 seconds as an example
    capturer.close()
    print(f"Audio captured and saved to {audio_file_path}")

    # 2. Transcribe audio to text
    asr = WhisperASR("medium.en")
    transcription = asr.transcribe(audio_file_path)
    print(f"Transcription: {transcription}")

    # 3. Determine if the text is visualizable
    parser = OpenAIParser()
    if not parser.generate_prompt(transcription):
        print("The text is not visualizable.")
        return

    # 4. Generate a descriptive prompt for image generation
    prompt = parser.generate_prompt(transcription)
    print(f"Generated Prompt: {prompt}")

    # 5. Generate image based on the prompt
    # image_generator = TextToImage()  # Assume TextToImage class is available
    # image_path = image_generator.generate_image(prompt)
    # print(f"Image generated and saved to {image_path}")

    # 6. Display the generated image
    # display = Display()  # Assume Display class is available
    # display.show_image(image_path)

    # Clean up the temporary audio file
    os.remove(audio_file_path)


if __name__ == "__main__":
    main()
