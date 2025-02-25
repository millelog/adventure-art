"""
environment_analyzer.py

Module to analyze transcripts and update environment descriptions based on new information.
Uses OpenAI GPT-4o to detect significant environmental changes.
"""

import openai
import json
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import environment_store
from adventure_art.server import scene_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# This will be imported from app.py to avoid circular imports
emit_environment_update = None

def set_emit_callback(callback_function):
    """Set the callback function for emitting environment updates."""
    global emit_environment_update
    emit_environment_update = callback_function

def analyze_transcript(transcript):
    """
    Analyzes a transcript to determine if the environment description needs to be updated.
    
    Parameters:
        transcript (str): The transcribed text to analyze.
        
    Returns:
        updated_environment (str): The updated environment description if an update is needed, 
                                  or None if no update is needed.
    """
    # Check if environment is locked against automatic updates
    if environment_store.is_environment_locked():
        print("Environment is locked, skipping automatic update")
        return None
        
    # Check if we have a valid transcript
    if not transcript or len(transcript.strip()) < 3:
        print("No valid transcript to analyze for environment updates")
        return None
    
    # Get the current environment description
    current_environment = environment_store.get_environment()
    current_description = current_environment.get('description', '')
    
    # Get the previous scene prompt for context
    previous_prompt = scene_store.get_last_prompt()
    previous_prompt_section = ""
    if previous_prompt:
        previous_prompt_section = (
            "Previous Scene Description:\n"
            f"{previous_prompt}\n\n"
            "Consider the previous scene description as additional context, but prioritize the transcript "
            "for determining if the environment has changed significantly."
        )
    
    # Define the function for structured output
    functions = [
        {
            "name": "update_environment",
            "description": "Update the environment description based on transcript analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "needs_update": {
                        "type": "boolean",
                        "description": "Whether the environment needs to be updated based on the transcript"
                    },
                    "environment_description": {
                        "type": "string",
                        "description": "The new environment description (only if needs_update is true). Must ONLY describe the physical setting (location, atmosphere, time of day, weather, terrain features) without ANY characters, actions, or narrative elements."
                    }
                },
                "required": ["needs_update"]
            }
        }
    ]
    
    # Build the prompt for the language model
    system_message = (
        "You analyze D&D session transcripts to maintain an accurate environment description. "
        "You only update the description when there's clear evidence of a significant location/setting change. "
        "IMPORTANT: Environment descriptions must NEVER include characters, actions, or narrative elements - "
        "they should ONLY describe the physical setting itself (location, atmosphere, time of day, weather, terrain). "
        "Your output should be structured using the function provided."
    )
    
    user_message = (
        "You are an environment analyzer for a D&D game. Your job is to maintain a concise description of the current "
        "environment or setting where the game is taking place. You'll analyze new transcript snippets to determine if "
        "the environment has changed significantly, and if so, how to update the description.\n\n"
        "Guidelines:\n"
        "- Keep the environment description brief (under 100 words) but informative\n"
        "- Focus ONLY on physical setting elements that would appear in an image (location, atmosphere, time of day, weather, etc.)\n"
        "- NEVER include characters, character actions, or narrative elements in the environment description\n"
        "- The environment description should be universally applicable regardless of what characters are doing in the scene\n"
        "- Only update the description if there's clear evidence in the transcript that the setting has changed\n"
        "- Maintain consistency with previous descriptions unless directly contradicted\n"
        "- Be conservative about making changes - don't change the environment for minor details\n\n"
        "Current Environment Description:\n"
        f"{current_description}\n\n"
        + (f"{previous_prompt_section}\n\n" if previous_prompt else "")
        + "New Transcript Snippet:\n"
        f"{transcript}\n\n"
        "Analyze this transcript and determine if the environment has changed significantly. "
        "If yes, provide a new complete environment description that ONLY describes the physical setting. "
        "If no, indicate no update is needed."
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
            function_call={"name": "update_environment"},
            max_tokens=500,
            temperature=0.3  # Lower temperature for more conservative updates
        )
        
        # Extract the function call arguments
        function_args = json.loads(response.choices[0].message.function_call.arguments)
        
        # Check if update is needed
        if not function_args.get("needs_update", False):
            print("No environment update needed")
            return None
        else:
            # Get the new environment description
            new_description = function_args.get("environment_description", "").strip()
            
            if not new_description:
                print("No valid environment description provided")
                return None
                
            # Additional check to filter out character names and actions
            if contains_character_elements(new_description, transcript):
                print("Environment description contains character elements, filtering...")
                new_description = filter_character_elements(new_description)
                
            print("Updating environment description")
            # Update the environment store
            environment_store.update_environment(new_description)
            
            # Emit the update via socket if the callback is set
            if emit_environment_update:
                emit_environment_update(new_description)
                
            return new_description
            
    except Exception as e:
        print(f"Error analyzing environment: {e}")
        return None

def contains_character_elements(description, transcript):
    """
    Check if the environment description contains character names or actions.
    This is a simple heuristic check that can be improved.
    
    Parameters:
        description (str): The environment description to check
        transcript (str): The original transcript to compare against
        
    Returns:
        bool: True if character elements are detected, False otherwise
    """
    # Extract potential character names from transcript (words starting with uppercase)
    words = transcript.split()
    potential_names = [word for word in words if word and word[0].isupper() and len(word) > 2]
    
    # Check if any potential names appear in the description
    for name in potential_names:
        if name in description:
            return True
    
    # Check for action verbs that might indicate character actions
    action_verbs = ["leads", "walks", "runs", "sits", "stands", "moves", "travels", "fights", "speaks"]
    for verb in action_verbs:
        if f" {verb} " in f" {description} ":
            return True
            
    return False

def filter_character_elements(description):
    """
    Attempt to filter out character elements from the environment description.
    This is a simple implementation that can be improved.
    
    Parameters:
        description (str): The environment description to filter
        
    Returns:
        str: The filtered environment description
    """
    # Split into sentences
    sentences = description.split('. ')
    filtered_sentences = []
    
    for sentence in sentences:
        # Skip sentences that likely contain character actions
        action_verbs = ["leads", "walks", "runs", "sits", "stands", "moves", "travels", "fights", "speaks"]
        if any(f" {verb} " in f" {sentence.lower()} " for verb in action_verbs):
            continue
            
        filtered_sentences.append(sentence)
    
    # If we filtered everything, return a generic version of the first sentence
    if not filtered_sentences and sentences:
        first_sentence = sentences[0]
        # Try to extract just the environment part
        if "with" in first_sentence:
            return first_sentence.split("with")[0].strip() + "."
        else:
            return first_sentence + "."
    
    return '. '.join(filtered_sentences) + ('.' if filtered_sentences and not filtered_sentences[-1].endswith('.') else '')

# Example usage for testing:
if __name__ == "__main__":
    sample_transcript = (
        "The party leaves the dark forest and emerges onto a vast open plain. The sun is setting, "
        "casting long shadows across the tall grass. In the distance, mountains can be seen."
    )
    updated_env = analyze_transcript(sample_transcript)
    print("Updated Environment:" if updated_env else "No update needed")
    if updated_env:
        print(updated_env) 