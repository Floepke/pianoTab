from pydantic import BaseModel, Field
from file.articulation import Articulation
from file.inherit_field import InheritMixin
from typing import List, TYPE_CHECKING, Literal, Union, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

class Note(InheritMixin, BaseModel):
    # Core note fields
    id: int = Field(default=0)
    time: float = Field(default=0.0, ge=0.0)
    duration: float = Field(default=256.0, ge=0.0)
    pitch: int = Field(default=40, ge=1, le=88)
    velocity: int = Field(default=80, ge=0, le=127)
    articulation: List[Articulation] = Field(default_factory=list)
    hand: Literal['<', '>'] = Field(default='>')
    
    # Private storage for inheritable fields (with aliases for JSON serialization)
    _color: Optional[str] = Field(default=None, alias='color', description="Color of the note, None to inherit from globalNote")
    _colorMidiNote: Optional[str] = Field(default=None, alias='colorMidiNote', description="MIDI note color, None to inherit from globalNote")
    _blackNoteDirection: Optional[Literal['^', 'v']] = Field(default=None, alias='blackNoteDirection', description="Black note direction, None to inherit from globalNote")
    
    # Score reference (not serialized to JSON)
    score: Optional['SCORE'] = Field(default=None, exclude=True)

    # Inheritance configuration (public -> (private, path, default))
    _INHERIT_CONFIG = {
        'color': ('_color', 'properties.globalNote.color', '#000000'),
        'colorMidiNote': ('_colorMidiNote', 'properties.globalNote.colorMidiNote', '#000000'),
        'blackNoteDirection': ('_blackNoteDirection', 'properties.globalNote.blackNoteDirection', 'v'),
    }
    
    class Config:
        extra = 'ignore'  # Need to use 'ignore' because we access fields via public names (e.g., note.color) which are handled by __getattribute__
        use_enum_values = True
        arbitrary_types_allowed = True
        populate_by_name = True
    
    def __init__(self, **data):
        # Extract score reference to set after initialization
        score = data.pop('score', None)
        super().__init__(**data)
        if score is not None:
            object.__setattr__(self, 'score', score)
    
    # InheritMixin provides __getattribute__/__setattr__/set_score_reference
    
    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        private_name = f'_{field_name}' if not field_name.startswith('_') else field_name
        return super().__getattribute__(private_name)
    
    # set_score_reference inherited from InheritMixin

# Add properties after class definition to avoid interfering with Pydantic initialization
