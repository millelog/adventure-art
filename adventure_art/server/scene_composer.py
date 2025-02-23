"""
scene_composer.py

Module to generate a detailed narrative scene description based on a transcript and
stored character details. This module retrieves character data from the file-based
character store and composes a prompt for the OpenAI language model.
"""

import openai
import re
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import character_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def compose_scene(transcript):
    """
    Composes a focused scene description based on the session transcript and stored character details.
    Identifies a key event and generates a concise description optimized for image generation.
    Provides all character details to the language model which will determine relevance.
    Returns None if no valid scene can be composed.
    
    Parameters:
        transcript (str): The transcribed text of the D&D session.
    
    Returns:
        scene_description (str): A concise, focused description of the key event in the scene.
        None: If no valid scene can be composed.
    """
    # Check if we have a valid transcript
    if not transcript or len(transcript.strip()) < 3:
        print("No valid transcript to compose scene from")
        return None
        
    # Basic validation to check if transcript seems to be in English
    common_english_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'is', 'are', 'and'}
    words = set(transcript.lower().split())
    if not any(word in common_english_words for word in words):
        print("Transcript appears to be non-English or invalid")
        return None
    
    # Retrieve all character data
    all_characters = character_store.get_all_characters()
    
    # Format all character details as a string
    character_details = []
    for char_id, data in all_characters.items():
        char_desc = f"{data.get('name', char_id)}: {data.get('description', 'No description provided')}"
        character_details.append(char_desc)
    
    if character_details:
        character_details = "\n\n".join(character_details)
    else:
        character_details = "No character data available."
    
    # Build the prompt for the language model with specific constraints
    prompt = (
        "You are a focused scene descriptor for a D&D session. Your task is to identify the most visually interesting "
        "key event from the transcript and describe it in a clear, concise way that's optimized for image generation.\n\n"
        "Guidelines:\n"
        "- Focus on ONE key moment or action\n"
        "- Only include characters that are actually mentioned or implied in the transcript\n"
        "- Keep descriptions under 200 words\n"
        "- Use clear, specific visual language\n"
        "- Prioritize action and emotion over complex details\n"
        "- For any characters you include, maintain consistency with their provided descriptions\n"
        "- If no clear action is described, create a simple portrait or scene of the mentioned characters\n"
        "- Avoid complex lighting or camera instructions\n\n"
        "Available Characters:\n"
        f"{character_details}\n\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        "Generate a concise scene description, only including characters that are relevant to this specific moment:"
    )
    
    try:
        # Call the OpenAI chat completion API with tighter constraints
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a concise D&D scene descriptor focused on clear, imageable moments. "
                 "Only include characters that are actually mentioned or implied in the transcript, maintaining consistency with their descriptions."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Get the scene description
        scene_description = response.choices[0].message.content.strip()
        return scene_description
        
    except Exception as e:
        print(f"Error generating scene description: {e}")
        return None

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party enters a dimly lit tavern. Gandalf sits in the corner, quietly observing the newcomers."
    )
    description = compose_scene(sample_transcript)
    print("Generated Scene Description:")
    print(description)
