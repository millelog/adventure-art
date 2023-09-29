import openai
import json
from config import OPENAI_API_KEY
from database.models import Scene
from utils.utils import scene_to_text



class OpenAIParser:
    def __init__(self):
        # Initialize the OpenAI API client
        openai.api_key = OPENAI_API_KEY

    def generate_prompt(self, current_scene: Scene, raw_text: str) -> str:
        functions = [
            {
                "name": "if_visualizable_then_generate_image",
                "description": "generates an image for Dungeons and Dragons visualiziation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_prompt": {"type": "string"},
                    },
                    "required": ["image_prompt"],
                },
            }
        ]

        messages = [
            {"role": "system",
             "content": f"You are a helpful assistant for determining visualizability and generating image prompts."},
            {"role": "system",
             "content": scene_to_text(current_scene)},  # Providing scene and characters info to the model
            {"role": "user",
             "content": f"Generate an image for the following section of a Dungeons and Dragons session if there is something that is visualizable: {raw_text}"}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions
        )

        response_message = response['choices'][0]['message']

        if response_message.get('function_call'):
            # Parse arguments from a JSON string to a dictionary
            arguments = json.loads(response_message['function_call']['arguments'])
            # Extract the generated prompt from the arguments dictionary
            generated_prompt = arguments['image_prompt']
            return generated_prompt
        else:
            # Handle cases where the function call did not produce the expected output
            return None


if __name__ == "__main__":
    parser = OpenAIParser()
    sample_transcription = "A dragon flies over a village, breathing fire."
    prompt = parser.generate_prompt(sample_transcription)
    print(f"Generated Prompt: {prompt}")
