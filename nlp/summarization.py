#nlp/summarization.py
import openai
import json
from database import DatabaseManager
from database.models import Base, Character, Scene, SceneCharacter, Narrative, CharacterDescriptor
from config.settings import OPENAI_API_KEY
from utils.utils import scene_to_text
class Summarizer:
    def __init__(self):
        openai.api_key = OPENAI_API_KEY
        self.db_manager = DatabaseManager()

    def summarize_scene(self, current_scene: Scene):
        # Call the OpenAI API to summarize the text
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            prompt=f"Summarize the following scene and character descriptions: {scene_to_text(current_scene)}"
        )

        summary = response['choices'][0]['text'].strip()

        # Update the narrative in the database with the summary
        narrative = self.db_manager.add_narrative(scene_id=current_scene.id, summary=summary)

        return narrative


if __name__ == "__main__":
    summarizer = Summarizer()
    summarized_narrative = summarizer.summarize_scene(scene_id=1)
    print(summarized_narrative.summary)
