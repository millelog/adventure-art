from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, create_engine, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Create a new SQLite database in memory
engine = create_engine('sqlite:///dnd_database.db', echo=True)

Base = declarative_base()

class Character(Base):
    __tablename__ = 'characters'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(Text)

    # Relationship to scenes in which this character appears
    scenes = relationship('SceneCharacter', back_populates='character')

    # Relationship to descriptors
    descriptors = relationship('CharacterDescriptor', back_populates='character')

class Scene(Base):
    __tablename__ = 'scenes'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    summary = Column(Text)
    is_active = Column(Boolean, default=True)

    # Relationship to characters in this scene
    characters = relationship('SceneCharacter', back_populates='scene')

class SceneCharacter(Base):
    __tablename__ = 'scene_characters'
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'))
    scene_id = Column(Integer, ForeignKey('scenes.id'))
    is_present = Column(Boolean, default=True)

    # Relationships
    character = relationship('Character', back_populates='scenes')
    scene = relationship('Scene', back_populates='characters')

class CharacterDescriptor(Base):
    __tablename__ = 'character_descriptors'
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('characters.id'))
    scene_id = Column(Integer, ForeignKey('scenes.id'))
    descriptor = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    character = relationship('Character', back_populates='descriptors')
    scene = relationship('Scene')  # No back_populates here to avoid a circular relationship

class Narrative(Base):
    __tablename__ = 'narratives'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    summary = Column(Text)
    scene_id = Column(Integer, ForeignKey('scenes.id'))

    # Relationship to Scene
    scene = relationship('Scene')

# Create all tables
Base.metadata.create_all(engine)

# Create a new session
Session = sessionmaker(bind=engine)
session = Session()

# Now you can use `session` to interact with the database
