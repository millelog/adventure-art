"""
scene_composer.py

Module to generate a detailed narrative scene description based on a transcript and
stored character details. This module retrieves character data from the file-based
character store and composes a prompt for the OpenAI language model.
"""

import openai
import re
import json
import random  # Add import for randomization
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import character_store
from adventure_art.server import environment_store
from adventure_art.server import scene_store
from adventure_art.server import style_store

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
    
    # Format all character details as a list and shuffle it for randomization
    character_details = []
    for char_id, data in all_characters.items():
        char_desc = f"{data.get('name', char_id)}: {data.get('description', 'No description provided')}"
        character_details.append(char_desc)
    
    # Randomize the order of character details to avoid positional bias
    random.shuffle(character_details)
    
    if character_details:
        character_details_text = "\n\n".join(character_details)
    else:
        character_details_text = "No character data available."
    
    # Get the current environment description
    environment_data = environment_store.get_environment()
    environment_description = environment_data.get('description', 'No specific environment defined.')
    
    # Get the previous scene prompt for continuity
    previous_prompt = scene_store.get_last_prompt()
    previous_prompt_section = ""
    if previous_prompt:
        previous_prompt_section = (
            "Previous Scene Description:\n"
            f"{previous_prompt}\n\n"
            "Use the previous scene description to maintain visual consistency where appropriate, "
            "but focus on the new action or moment described in the current transcript."
        )
    
    # Get the style directive
    style_directive = style_store.get_style_directive()
    
    # Define the function for structured output
    functions = [
        {
            "name": "generate_scene_description",
            "description": "Generate a focused scene description based on the transcript",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene_description": {
                        "type": "string",
                        "description": "A concise, focused description of the key event in the scene, optimized for image generation. Should be under 200 words and focus on one key moment or action."
                    },
                    "character_names": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of character names that appear in the scene description."
                    }
                },
                "required": ["scene_description", "character_names"]
            }
        }
    ]
    
    # Build the prompt for the language model with specific constraints
    system_message = (
        "You are a concise D&D scene descriptor focused on clear, imageable moments. "
        "Only include characters that are actually mentioned or implied in the transcript, maintaining consistency with their descriptions "
        "and ensuring the scene is set within the provided environment. Your output should be structured using the function provided. "
        "Always use character names explicitly in your descriptions to maintain character consistency across scenes."
    )
    
    user_message = (
        "You are a focused scene descriptor for a D&D session. Your task is to identify the most visually interesting "
        "key event from the transcript and describe it in a clear, concise way that's optimized for image generation.\n\n"
        "Guidelines:\n"
        "- Focus on ONE key moment or action\n"
        "- Only include characters that are actually mentioned or implied in the transcript\n"
        "- ALWAYS use character names explicitly in your description, even if they're only implied in the transcript\n"
        "- If a character is referenced indirectly in the transcript (e.g., 'the wizard'), use their proper name (e.g., 'Gandalf')\n"
        "- Keep descriptions under 200 words\n"
        "- Use clear, specific visual language\n"
        "- Prioritize action and emotion over complex details\n"
        "- For any characters you include, maintain consistency with their provided descriptions\n"
        "- If no clear action is described, create a simple portrait or scene of the mentioned characters\n"
        "- Avoid complex lighting or camera instructions\n"
        "- Make the scene consistent with the current environment description\n"
        f"- {'' if not previous_prompt else 'Maintain visual continuity with the previous scene where appropriate'}\n\n"
        "Visual Style Guidelines:\n"
        f"{style_directive}\n\n"
        "Current Environment:\n"
        f"{environment_description}\n\n"
        + (f"{previous_prompt_section}\n\n" if previous_prompt else "")
        + "Available Characters:\n"
        f"{character_details_text}\n\n"
        "Transcript:\n"
        f"{transcript}\n\n"
        "Generate a concise scene description, only including characters that are relevant to this specific moment and ensuring "
        "it fits within the described environment. Always refer to characters by their proper names to maintain consistency."
    )
    
    try:
        # Call the OpenAI chat completion API with function calling
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            functions=functions,
            function_call={"name": "generate_scene_description"},
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract the function call arguments
        function_args = json.loads(response.choices[0].message.function_call.arguments)
        
        # Get the scene description
        scene_description = function_args.get("scene_description", "").strip()
        
        # Get the character names (for potential future use)
        character_names = function_args.get("character_names", [])
        
        if not scene_description:
            print("No valid scene description generated")
            return None
        
        # Store the scene description for future reference
        scene_store.update_last_prompt(scene_description)
        
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
