"""
scene_composer.py

Module to generate a detailed narrative scene description based on a transcript and
stored character details. This module retrieves main character data from the file-based
character store and composes a prompt for the OpenAI language model.
"""

import openai
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import character_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
        # Call the OpenAI chat completion API
        response = client.chat.completions.create(
            model="gpt-4",  # or "gpt-3.5-turbo" if you prefer
            messages=[
                {"role": "system", "content": "You are a creative D&D scene description generator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        scene_description = response.choices[0].message.content.strip()
        return scene_description
    except openai.APIError as e:
        raise Exception(f"OpenAI API error: {str(e)}")
    except openai.APIConnectionError as e:
        raise Exception(f"Error connecting to OpenAI API. Please check your internet connection and API key: {str(e)}")
    except Exception as e:
        raise Exception(f"Error generating scene description: {str(e)}")

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party enters a dimly lit tavern. Shadows dance along the walls as a mysterious figure "
        "sits in the corner, quietly observing the newcomers."
    )
    description = compose_scene(sample_transcript)
    print("Generated Scene Description:")
    print(description)
