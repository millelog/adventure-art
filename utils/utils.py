# utils/utils.py

def scene_to_text(current_scene):
    """
    Convert a Scene object into a descriptive text string.

    Args:
        current_scene (Scene): The scene object to be converted to text.

    Returns:
        str: A string describing the scene and characters.
    """
    # Get characters and their descriptions from the current scene
    characters_info = []
    for character in current_scene.characters:
        char_general_description = character.character.description
        char_scene_descriptors = ', '.join([descriptor.descriptor for descriptor in character.character.descriptors])
        char_info = f"{character.character.name} is {char_general_description} and in this scene is described as: {char_scene_descriptors}"
        characters_info.append(char_info)
    characters_info_str = '; '.join(characters_info)

    # Prepare the scene and characters info string
    scene_and_characters_info = (
        f"The current scene is {current_scene.title}, described as: {current_scene.summary}. "
        f"The characters present are: {characters_info_str}."
    )

    return scene_and_characters_info

# Now you can import scene_to_text from utils.py in other scripts and use it to convert a Scene object to text.
