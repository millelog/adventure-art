# nlp/__init__.py

from .scene_understanding import scene_processor
from .named_entity_recognition import named_entity_recognizer
# Import any other functions or classes you want to be accessible from the nlp package

__all__ = [
    'scene_processor',
    'named_entity_recognizer',
    # List any other functions or classes you want to be accessible from the nlp package
]

