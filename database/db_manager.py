#database/db_manager.py
from datetime import datetime
from database.models import Base, Character, Scene, SceneCharacter, Narrative, CharacterDescriptor
from nlp.summarization import Summarization
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self, db_url='sqlite:///dnd_database.db'):
        self.engine = create_engine(db_url, echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def create_all(self):
        Base.metadata.create_all(self.engine)

    def update_character_descriptors(self, name, descriptors, scene):
        character = self.get_character_by_name(name)
        if character is None:
            character = Character(name=name)
            self.session.add(character)
            self.session.commit()  # Ensure character is committed to get an ID

        for descriptor in descriptors:
            char_descriptor = CharacterDescriptor(
                character_id=character.id,
                scene_id=scene.id,
                descriptor=descriptor
            )
            self.session.add(char_descriptor)
        self.session.commit()
        return character

    # The summarize_scene function
    def summarize_scene(scene):
        # Call the summarization module to generate a summary for the scene
        # Assume summarize is a function in the summarization module
        summary = Summarization.summarize(scene)
        return summary
    def create_new_scene(self, scene_description, characters_present, characters_descriptors):
        # End the current scene
        ended_scene = self.end_current_scene()

        # Summarize the ended scene
        if ended_scene:
            summary = self.summarize_scene(ended_scene)
            self.add_narrative(summary, ended_scene)  # Assume timestamp is handled within add_narrative

        # Create a new scene
        new_scene = Scene(title=scene_description, summary=scene_description, is_active=True)
        self.session.add(new_scene)
        self.session.commit()

        # Update characters and descriptors
        for char_name in characters_present:
            character = self.get_character_by_name(char_name)
            if character is None:
                character = self.add_character(char_name, "")
            self.link_character_scene(character, new_scene)

            # Update character descriptors if provided
            if char_name in characters_descriptors:
                self.update_character_descriptors(char_name, characters_descriptors[char_name], new_scene)

        return new_scene

    def update_current_scene(self, scene, scene_title, scene_description, characters_present, characters_descriptors):
        # Update scene description
        scene.title = scene_title
        scene.summary = scene_description
        self.session.commit()  # Commit the updated scene description

        # Update characters and descriptors
        for char_name in characters_present:
            character = self.get_character_by_name(char_name)
            if character is None:
                character = self.add_character(char_name, "")  # Assuming empty string for description
            self.link_character_scene(character, scene)  # Assuming character is present in the scene

            # Update character descriptors if provided
            if char_name in characters_descriptors:
                self.update_character_descriptors(char_name, characters_descriptors[char_name], scene)

        return scene  # Return the updated scene object

    def end_current_scene(self):
        current_scene = self.get_current_scene()
        if current_scene:
            current_scene.is_active = False
            self.session.commit()
        return current_scene

    def get_current_scene(self):
        # Get the first active scene
        current_scene = self.session.query(Scene).filter_by(is_active=True).first()
        return current_scene

    def add_character(self, name, description):
        character = Character(name=name, description=description)
        self.session.add(character)
        self.session.commit()
        return character

    def add_scene(self, title, summary):
        scene = Scene(title=title, summary=summary)
        self.session.add(scene)
        self.session.commit()
        return scene

    def link_character_scene(self, character, scene, is_present=True):
        scene_character = SceneCharacter(character=character, scene=scene, is_present=is_present)
        self.session.add(scene_character)
        self.session.commit()
        return scene_character

    def add_narrative(self, summary, scene, timestamp=None):
        if timestamp is None:
            timestamp = datetime.utcnow()
        narrative = Narrative(timestamp=timestamp, summary=summary, scene=scene)
        self.session.add(narrative)
        self.session.commit()
        return narrative

    def get_character_by_name(self, name):
        return self.session.query(Character).filter_by(name=name).first()

    def get_scene_by_title(self, title):
        return self.session.query(Scene).filter_by(title=title).first()

    def get_narrative_by_scene(self, scene):
        return self.session.query(Narrative).filter_by(scene=scene).all()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    db_manager.create_all()
    # Further testing code if needed...
