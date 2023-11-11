from openai import OpenAI
import json
from config import OPENAI_API_KEY, OPENAI_MODEL
from database.models import Scene
from utils.utils import scene_to_text

class OpenAIParser:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_prompt(self, current_scene: Scene, raw_text: str) -> str:
        functions = [
            {
                "name": "if_visualizable_then_generate_image",
                "description": "generates an image for Dungeons and Dragons visualization",
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
             "content": "You are a helpful assistant for determining visualizability and generating image prompts."},
            {"role": "system",
             "content": scene_to_text(current_scene)},  # Providing scene and characters info to the model
            {"role": "user",
             "content": f"Generate an image for the following section of a Dungeons and Dragons session if there is something that is visualizable: {raw_text}"}
        ]

        response = self.client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            functions=functions
        )

        # Adjusting response parsing to match the new response object format
        response_message = response.choices[0].message

        # Check if 'function_call' exists and is not None
        if hasattr(response_message, 'function_call') and response_message.function_call:
            # Directly access attributes of the Pydantic model
            function_call = response_message.function_call
            function_name = function_call.name
            function_arguments = function_call.arguments

            # Check if the function call is the expected one
            if function_name == "if_visualizable_then_generate_image":
                # Parse arguments from a JSON string to a dictionary
                arguments = json.loads(function_arguments)
                # Extract the generated prompt from the arguments dictionary
                generated_prompt = arguments.get('image_prompt')
                return generated_prompt

        # Handle cases where the function call did not produce the expected output
        return None


if __name__ == "__main__":
    parser = OpenAIParser()
    sample_transcription = "A dragon flies over a village, breathing fire."
    prompt = parser.generate_prompt(sample_transcription)
    print(f"Generated Prompt: {prompt}")
