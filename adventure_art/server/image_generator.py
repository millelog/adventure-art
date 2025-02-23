"""
image_generator.py

Module to generate an image based on a scene description using the OpenAI image generation API (DALL-E 3).
It receives a textual scene description and returns the URL of the generated image.
"""

import openai
import re
from adventure_art.server.config import OPENAI_API_KEY

# Initialize the OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def extract_reference_images(scene_description):
    """
    Extract reference image URLs from the scene description.
    
    Parameters:
        scene_description (str): The scene description text
        
    Returns:
        tuple: (clean_description, list of reference image URLs)
    """
    # Split on the reference images section if it exists
    parts = scene_description.split("\n\nReference images for character appearances:\n")
    
    if len(parts) == 1:
        return scene_description, []
    
    clean_description = parts[0]
    reference_urls = parts[1].strip().split("\n")
    return clean_description, reference_urls

def generate_image(scene_description):
    """
    Generates an image based on the provided scene description using the OpenAI image generation API.
    Handles reference images for character consistency.
    Returns None if no valid scene description is provided or if image generation fails.
    
    Parameters:
        scene_description (str): A detailed narrative description of the scene.
    
    Returns:
        image_url (str): URL of the generated image.
        None: If image generation fails or no valid description is provided.
    """
    if not scene_description:
        print("No valid scene description provided for image generation")
        return None
        
    try:
        # Extract any reference images from the description
        clean_description, reference_images = extract_reference_images(scene_description)
        
        # Build the prompt with reference images if available
        if reference_images:
            prompt = (
                f"{clean_description}\n\n"
                "Please maintain visual consistency with these character reference images:\n"
                f"{', '.join(reference_images)}"
            )
        else:
            prompt = clean_description
        
        # Call the OpenAI images.generate method to create an image from the scene description.
        response = client.images.generate(
            model="dall-e-3",  # Specify the model name
            prompt=prompt,
            n=1,
            size="1792x1024"  # Adjust size as necessary
        )
        # Extract and return the image URL from the API response.
        image_url = response.data[0].url
        return image_url
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
        url = generate_image(sample_description)
        print("Generated image URL:", url)
    except Exception as error:
        print("Error:", error)
