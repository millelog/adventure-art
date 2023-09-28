#nlp/summarization.py
import openai
import json
from database import DatabaseManager
from database.models import Base, Character, Scene, SceneCharacter, Narrative, CharacterDescriptor
from config.settings import OPENAI_API_KEY
class Summarizer:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.db_manager = DatabaseManager()

    def summarize_scene(self, scene_id):
        # Fetch the scene, characters, and their descriptors from the database
        scene = self.db_manager.session.query(Scene).filter_by(id=scene_id).first()
        scene_characters = self.db_manager.session.query(SceneCharacter).filter_by(scene_id=scene_id).all()

        # Prepare data for summarization
        characters_descriptors = {}
        for scene_character in scene_characters:
            character = scene_character.character
            descriptors = self.db_manager.session.query(CharacterDescriptor).filter_by(
                character_id=character.id, scene_id=scene_id
            ).all()
            characters_descriptors[character.name] = [descriptor.descriptor for descriptor in descriptors]

        # Create a textual representation of the scene and characters for summarization
        scene_description = scene.summary
        characters_description = '. '.join(
            [f"{name} is {', '.join(descriptors)}." for name, descriptors in characters_descriptors.items()]
        )
        text_to_summarize = f"{scene_description}. {characters_description}"

        # Call the OpenAI API to summarize the text
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            prompt=f"Summarize the following scene and character descriptions: {text_to_summarize}",
            max_tokens=150  # Limit the summary to a reasonable length
        )

        summary = response['choices'][0]['text'].strip()

        # Update the narrative in the database with the summary
        narrative = self.db_manager.add_narrative(scene_id=scene_id, summary=summary)

        return narrative


if __name__ == "__main__":
    summarizer = Summarizer()
    summarized_narrative = summarizer.summarize_scene(scene_id=1)
    print(summarized_narrative.summary)
