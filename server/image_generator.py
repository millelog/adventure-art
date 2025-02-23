"""
image_generator.py

Module to generate an image based on a scene description using the OpenAI image generation API (DALL-E 3).
It receives a textual scene description and returns the URL of the generated image.
"""

import openai
from config import OPENAI_API_KEY

# Set the OpenAI API key (assumes same key is used for both text and image generation)
openai.api_key = OPENAI_API_KEY

def generate_image(scene_description):
    """
    Generates an image based on the provided scene description using the OpenAI image generation API.
    
    Parameters:
        scene_description (str): A detailed narrative description of the scene.
    
    Returns:
        image_url (str): URL of the generated image.
    """
    try:
        # Call the OpenAI Image API to generate an image from the scene description.
        response = openai.Image.create(
            prompt=scene_description,
            n=1,
            size="1024x1024"  # Adjust size as necessary
        )
        # Extract and return the image URL from the API response.
        image_url = response['data'][0]['url']
        return image_url
    except Exception as e:
        raise Exception(f"Error generating image: {e}")

# Example usage for testing:
if __name__ == "__main__":
    sample_description = (
        "A dark, stormy night with a looming castle in the distance, "
        "illuminated by flashes of lightning, and a brave warrior standing guard."
    )
    try:
        url = generate_image(sample_description)
        print("Generated image URL:", url)
    except Exception as error:
        print("Error:", error)
