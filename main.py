import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import random
import glob
from input.audio_capture import AudioCapture
from asr.whisper_asr import WhisperASR
from api_parser.openai_parser import OpenAIParser
from nlp.named_entity_recognition import named_entity_recognizer
from nlp.scene_understanding import scene_processor
from database.db_manager import DatabaseManager
from utils.utils import scene_to_text

# Import the image generation and GUI modules when they are available
# from image_generator.text_to_image import TextToImage
# from gui.display import Display

def main():
    # Initialize Database Manager
    current_scene = None
    db_manager = DatabaseManager()
    scene_processor_instance = scene_processor()
    named_entity_recognizer_instance = named_entity_recognizer()
    parser_instance = OpenAIParser()


    debug = True  # Set debug mode

    if debug:
        labeled_audio_files = glob.glob('dnd_sample/*.wav')  # Adjust path and extension accordingly
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
        scene_processor_instance.process_scene_text(transcription)

        # 4. Named Entity Recognition: Identify characters and scenes
        named_entity_recognizer_instance.identify_named_entities(transcription)

        current_scene = db_manager.get_current_scene()
        print(scene_to_text(current_scene))

        # 6. Generate a descriptive prompt for image generation
        prompt = parser_instance.generate_prompt(current_scene, transcription)

        if not prompt:
            print("Text is not visualizable")
            continue

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
