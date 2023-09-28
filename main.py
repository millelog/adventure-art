import os
from dotenv import load_dotenv
import random
import glob

# Load environment variables from .env file
load_dotenv()

from input.audio_capture import AudioCapture
from asr.whisper_asr import WhisperASR
from api_parser.openai_parser import OpenAIParser
from nlp.named_entity_recognition import identify_named_entities
from nlp.scene_understanding import process_scene_text
from database import DatabaseManager


# Import the image generation and GUI modules when they are available
# from image_generator.text_to_image import TextToImage
# from gui.display import Display

def main():
    # Initialize Database Manager
    db_manager = DatabaseManager()

    debug = True  # Set debug mode

    if debug:
        labeled_audio_files = glob.glob('path_to_labeled_audio_files/*.wav')  # Adjust path and extension accordingly
        file_pointer = random.randint(0, len(labeled_audio_files) - 1)  # Randomly initialize the file pointer

    while True:  # Infinite loop, can be exited with CTRL + C or some exit condition
        # 1. Capture audio
        if debug:
            audio_file_path = labeled_audio_files[file_pointer]  # Get the current file
            file_pointer = (file_pointer + 1) % len(
                labeled_audio_files)  # Move the pointer to the next file, loop back to 0 at the end of the list
        else:
            capturer = AudioCapture(debug=True)
            audio_file_path = capturer.capture_audio(30)  # Capture for 5 seconds as an example
            capturer.close()

        print(f"Audio captured and saved to {audio_file_path}")

        # 2. Transcribe audio to text
        asr = WhisperASR("medium.en")
        transcription = asr.transcribe(audio_file_path)
        print(f"Transcription: {transcription}")

        # 3. Scene Understanding: Understand the current scene and update the database
        current_scene = process_scene_text(transcription)

        # 4. Named Entity Recognition: Identify characters and scenes
        current_scene = identify_named_entities(transcription, current_scene)

        print(current_scene)

        # 5. Determine if the text is visualizable
        parser = OpenAIParser()
        if not parser.generate_prompt(current_scene, transcription):
            print("The text is not visualizable.")
            continue  # Skip to the next iteration

        # 6. Generate a descriptive prompt for image generation
        prompt = parser.generate_prompt(transcription)
        print(f"Generated Prompt: {prompt}")

        # 7. Generate image based on the prompt
        # image_generator = TextToImage()  # Assume TextToImage class is available
        # image_path = image_generator.generate_image(prompt)
        # print(f"Image generated and saved to {image_path}")

        # 8. Display the generated image
        # display = Display()  # Assume Display class is available
        # display.show_image(image_path)

        # Clean up the temporary audio file
        if not debug:  # Don't remove files in debug mode
            os.remove(audio_file_path)

        if debug and file_pointer >= len(labeled_audio_files):
            break  # Exit loop after processing all files in debug mode

if __name__ == "__main__":
    main()
