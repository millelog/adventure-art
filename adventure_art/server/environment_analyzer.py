"""
environment_analyzer.py

Module to analyze transcripts and update environment descriptions based on new information.
Uses OpenAI GPT-4o to detect significant environmental changes.
"""

import openai
from adventure_art.server.config import OPENAI_API_KEY
from adventure_art.server import environment_store

# Set the OpenAI API key
client = openai.OpenAI(api_key=OPENAI_API_KEY)

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
    
    # Build the prompt for the language model
    prompt = (
        "You are an environment analyzer for a D&D game. Your job is to maintain a concise description of the current "
        "environment or setting where the game is taking place. You'll analyze new transcript snippets to determine if "
        "the environment has changed significantly, and if so, how to update the description.\n\n"
        "Guidelines:\n"
        "- Keep the environment description brief (under 100 words) but informative\n"
        "- Focus on physical setting elements that would appear in an image (location, atmosphere, time of day, weather, etc.)\n"
        "- Only update the description if there's clear evidence in the transcript that the setting has changed\n"
        "- Maintain consistency with previous descriptions unless directly contradicted\n"
        "- Be conservative about making changes - don't change the environment for minor details\n"
        "- Don't include character positions or temporary objects unless they're defining features of the location\n\n"
        "Current Environment Description:\n"
        f"{current_description}\n\n"
        "New Transcript Snippet:\n"
        f"{transcript}\n\n"
        "Does this transcript indicate a significant change to the environment? If yes, provide a new complete environment description. "
        "If no, respond with 'NO_UPDATE_NEEDED'."
    )
    
    try:
        # Call the OpenAI chat completion API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You analyze D&D session transcripts to maintain an accurate environment description. "
                 "You only update the description when there's clear evidence of a significant location/setting change."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3  # Lower temperature for more conservative updates
        )
        
        # Get the analysis result
        analysis_result = response.choices[0].message.content.strip()
        
        # Check if update is needed
        if "NO_UPDATE_NEEDED" in analysis_result:
            print("No environment update needed")
            return None
        else:
            print("Updating environment description")
            # Update the environment store
            environment_store.update_environment(analysis_result)
            return analysis_result
            
    except Exception as e:
        print(f"Error analyzing environment: {e}")
        return None

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