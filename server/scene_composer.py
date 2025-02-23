"""
scene_composer.py

Module to generate a detailed narrative scene description based on a transcript and
stored character details. This module retrieves main character data from the file-based
character store and composes a prompt for the OpenAI language model.
"""

import openai
from config import OPENAI_API_KEY
import character_store

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

def compose_scene(transcript):
    """
    Composes a detailed scene description based on the session transcript and stored character details.
    
    Parameters:
        transcript (str): The transcribed text of the D&D session.
    
    Returns:
        scene_description (str): A detailed narrative description of the current scene.
    """
    # Retrieve main character data from the character store.
    characters = character_store.get_all_characters()
    
    # Format the character details as a string for inclusion in the prompt.
    if characters:
        character_details = "\n".join(
            f"{name}: {data.get('description', 'No description provided')}" 
            for name, data in characters.items()
        )
    else:
        character_details = "No character data available."
    
    # Build the prompt for the language model.
    prompt = (
        "You are a creative storyteller for a Dungeons & Dragons session. Based on the following transcript and "
        "the main characters' details, generate a detailed scene description that captures the setting, mood, and character interactions.\n\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        "Main Characters:\n"
        f"{character_details}\n\n"
        "Scene Description:"
    )
    
    try:
        # Call the OpenAI completion API (using text-davinci-003 for this example).
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            temperature=0.7,
            n=1,
            stop=None
        )
        
        scene_description = response.choices[0].text.strip()
        return scene_description
    except Exception as e:
        raise Exception(f"Error generating scene description: {e}")

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party enters a dimly lit tavern. Shadows dance along the walls as a mysterious figure "
        "sits in the corner, quietly observing the newcomers."
    )
    description = compose_scene(sample_transcript)
    print("Generated Scene Description:")
    print(description)
