#nlp/scene_understanding.py
import openai
import json


def process_scene_text(text: str, current_scene):
    from database import DatabaseManager

    # Initialize your database manager
    db_manager = DatabaseManager()
    """Process the text to understand the scene and update the database."""

    functions = [
        {
            "name": "create_new_scene",
            "description": "Create a new scene entry in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene_description": {"type": "string"},
                    "characters_present": {"type": "array", "items": {"type": "string"}},
                    "characters_descriptors": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "required": ["scene_description", "characters_present", "characters_descriptors"]
            }
        },
        {
            "name": "update_current_scene",
            "description": "Update the current scene entry in the database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "scene": {"type": "object"},  # Assuming scene is passed as an object, adjust as needed
                    "scene_title": {"type": "string"},
                    "scene_description": {"type": "string"},
                    "characters_present": {"type": "array", "items": {"type": "string"}},
                    "characters_descriptors": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "required": ["scene", "scene_title", "scene_description", "characters_present", "characters_descriptors"]
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a helpful assistant for understanding scenes and characters. only respond with defined functions."},
        {"role": "user", "content": f"Process the following text to understand the scene and characters: {text}"},
        {"role": "user", "content": f"The most recent scene object is: {current_scene}"}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=messages,
        functions=functions,
    )

    response_message = response["choices"][0]["message"]

    if response_message.get("function_call"):
        function_name = response_message["function_call"]["name"]
        function_args = json.loads(response_message["function_call"]["arguments"])

        if function_name == "create_new_scene":
            return db_manager.create_new_scene(**function_args)
        elif function_name == "update_current_scene":
            return db_manager.update_current_scene(**function_args)

if __name__ == "__main__":
    text_sample = "In a dark and stormy night, Arthur and Merlin were devising a plan in the grand hall."
    current_scene = db_manager.get_latest_scene()  # Assume this method gets the latest scene from the database
    process_scene_text(text_sample, current_scene)
