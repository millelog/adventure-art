import openai
import json
from config import OPENAI_API_KEY


class OpenAIParser:
    def __init__(self):
        # Initialize the OpenAI API client
        openai.api_key = OPENAI_API_KEY

    def generate_prompt(self, raw_text: str) -> str:
        functions = [
            {
                "name": "if_visualizable_then_generate_image",
                "description": "generates an image for image generation",
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
            # Extract the generated prompt from the function response content
            generated_prompt = response_message['function_call']['arguments']['image_prompt']
            return generated_prompt
        else:
            # Handle cases where the function call did not produce the expected output
            return None


if __name__ == "__main__":
    parser = OpenAIParser()
    sample_transcription = "A dragon flies over a village, breathing fire."
    prompt = parser.generate_prompt(sample_transcription)
    print(f"Generated Prompt: {prompt}")