"""
scene_composer.py

Module to generate a detailed narrative scene description based on a transcript and
stored character details. This module retrieves main character data from the file-based
character store and composes a prompt for the OpenAI language model.
"""

import openai
import re
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import character_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def find_mentioned_characters(transcript, characters):
    """
    Find which characters from our character store are mentioned in the transcript.
    Uses fuzzy matching to catch variations of names.
    
    Parameters:
        transcript (str): The transcribed text
        characters (dict): Dictionary of character data
    
    Returns:
        dict: Dictionary containing only the mentioned characters
    """
    mentioned_characters = {}
    
    # Convert transcript to lowercase for case-insensitive matching
    transcript_lower = transcript.lower()
    
    for char_id, char_data in characters.items():
        # Check for character name in transcript
        char_name = char_data.get('name', char_id).lower()
        if char_name in transcript_lower:
            mentioned_characters[char_id] = char_data
            
    return mentioned_characters

def compose_scene(transcript):
    """
    Composes a focused scene description based on the session transcript and stored character details.
    Identifies a key event and generates a concise description optimized for image generation.
    Only includes details for characters that are actually mentioned in the transcript.
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
    # This helps catch cases where whisper returns non-English text
    common_english_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'is', 'are', 'and'}
    words = set(transcript.lower().split())
    if not any(word in common_english_words for word in words):
        print("Transcript appears to be non-English or invalid")
        return None
    
    # Retrieve all character data
    all_characters = character_store.get_all_characters()
    
    # Find which characters are mentioned in the transcript
    relevant_characters = find_mentioned_characters(transcript, all_characters)
    
    # Format the character details as a string, including reference images if available
    if relevant_characters:
        character_details = []
        for name, data in relevant_characters.items():
            char_desc = f"{name}: {data.get('description', 'No description provided')}"
            if 'image_url' in data:
                char_desc += f"\nReference image: {data['image_url']}"
            character_details.append(char_desc)
        character_details = "\n\n".join(character_details)
    else:
        character_details = "No relevant character data available."
    
    # Build the prompt for the language model with specific constraints
    prompt = (
        "You are a focused scene descriptor for a D&D session. Your task is to identify the most visually interesting "
        "key event from the transcript and describe it in a clear, concise way that's optimized for image generation.\n\n"
        "Guidelines:\n"
        "- Focus on ONE key moment or action\n"
        "- Include only the relevant characters involved in that moment\n"
        "- Keep descriptions under 200 words\n"
        "- Use clear, specific visual language\n"
        "- Prioritize action and emotion over complex details\n"
        "- Incorporate the visual details from character reference images when describing those characters\n"
        "- Maintain consistency with character appearances from their reference images\n"
        "- If no clear action is described, create a simple portrait or scene of the mentioned characters\n"
        "- Avoid complex lighting or camera instructions\n\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        "Relevant Characters (with reference images):\n"
        f"{character_details}\n\n"
        "Generate a concise scene description that maintains visual consistency with any provided character references:"
    )
    
    try:
        # Call the OpenAI chat completion API with tighter constraints
        response = client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better understanding of character references
            messages=[
                {"role": "system", "content": "You are a concise D&D scene descriptor focused on clear, imageable moments. "
                 "When character reference images are provided, ensure your description maintains visual consistency with those references."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Get the scene description
        scene_description = response.choices[0].message.content.strip()
        
        # If we have character reference images, include them in the final image generation prompt
        reference_images = [data.get('image_url') for data in relevant_characters.values() if 'image_url' in data]
        if reference_images:
            scene_description += "\n\nReference images for character appearances:\n" + "\n".join(reference_images)
        
        return scene_description
    except Exception as e:
        print(f"Error generating scene description: {e}")
        return None

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party enters a dimly lit tavern. Shadows dance along the walls as a mysterious figure "
        "sits in the corner, quietly observing the newcomers."
    )
    description = compose_scene(sample_transcript)
    print("Generated Scene Description:")
    print(description)
