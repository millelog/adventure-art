"""
image_generator.py

Module to generate an image based on a scene description using the Google Imagen 3.0 API.
It receives a textual scene description and returns the URL of the generated image.
"""

import os
from google import genai
from google.genai import types
import base64
from io import BytesIO
import tempfile
from pathlib import Path

# Get the API key from environment variable
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Initialize the Gen AI client
client = genai.Client(api_key=GEMINI_API_KEY)

def generate_image(scene_description):
    """
    Generates an image based on the provided scene description using the Google Imagen 3.0 API.
    Returns None if no valid scene description is provided or if image generation fails.
    
    Parameters:
        scene_description (str): A detailed narrative description of the scene.
    
    Returns:
        image_url (str): Path to the locally saved generated image.
        None: If image generation fails or no valid description is provided.
    """
    if not scene_description:
        print("No valid scene description provided for image generation")
        return None
        
    try:
        # Generate image using Imagen 3.0
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=scene_description,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio='16:9',  # Using widescreen ratio for better scene composition
            )
        )

        # Save the generated image to a temporary file
        if response.generated_images:
            # Create a temporary file with a .png extension
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                # Get the first generated image
                image_bytes = response.generated_images[0].image.image_bytes
                temp_file.write(image_bytes)
                return temp_file.name
        else:
            print("No images were generated")
            return None

    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Example usage for testing:
if __name__ == "__main__":
    sample_description = (
        "A dark, stormy night with a looming castle in the distance, "
        "illuminated by flashes of lightning, and a brave warrior standing guard."
    )
    try:
        path = generate_image(sample_description)
        print("Generated image saved at:", path)
    except Exception as error:
        print("Error:", error)