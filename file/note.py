from pydantic import BaseModel, Field
from file.articulation import Articulation
from typing import List, TYPE_CHECKING, Literal, Union, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

class Note(BaseModel):
    # Core note fields
    id: int = Field(default=0)
    time: float = Field(default=0.0)
    duration: float = Field(default=256.0)
    pitch: int = Field(default=40)
    velocity: int = Field(default=80)
    articulation: List[Articulation] = Field(default_factory=list)
    hand: Literal['<', '>'] = Field(default='>')
    
    # Inheritable fields - None means inherit from global properties
    color: Optional[str] = Field(default=None, description="Color of the note, None to inherit from globalNote")
    colorMidiNote: Optional[str] = Field(default=None, description="MIDI note color, None to inherit from globalNote")
    blackNoteDirection: Optional[Literal['^', 'v']] = Field(default=None, description="Black note direction, None to inherit from globalNote")
    
    # Score reference (not serialized to JSON)
    score: Optional['SCORE'] = Field(default=None, exclude=True)
    
    class Config:
        extra = 'forbid'
        use_enum_values = True
        arbitrary_types_allowed = True
    
    def __init__(self, **data):
        # Extract score reference to set after initialization
        score = data.pop('score', None)
        super().__init__(**data)
        if score is not None:
            object.__setattr__(self, 'score', score)
    
    def __getattribute__(self, name: str):
        """Handle property inheritance transparently."""
        # Allow access to private/special attributes and methods
        if (name.startswith('_') or name in ('dict', 'json', 'copy', '__fields__', 'Config', 'score') or
            hasattr(BaseModel, name)):
            return super().__getattribute__(name)
        
        # Get the stored value
        value = super().__getattribute__(name)
        
        # Check if this field should inherit (value is None)
        if value is None and name in ['color', 'colorMidiNote', 'blackNoteDirection']:
            return self._get_inherited_value(name)
        
        return value
    
    def _get_inherited_value(self, field_name: str):
        """Get the inherited value from global properties."""
        score = super().__getattribute__('score')
        if score is None:
            return self._get_default_value(field_name)
        
        if field_name == 'color':
            return score.properties.globalNote.color
        elif field_name == 'colorMidiNote':
            hand = super().__getattribute__('hand')
            if hand == '<':
                return score.properties.globalNote.colorLeftMidiNote
            elif hand == '>':
                return score.properties.globalNote.colorRightMidiNote
            return score.properties.globalNote.colorLeftMidiNote
        elif field_name == 'blackNoteDirection':
            return score.properties.globalNote.blackNoteDirection
        
        return self._get_default_value(field_name)
    
    def _get_default_value(self, field_name: str):
        """Get default values when no score reference."""
        defaults = {
            'color': '#000000',
            'colorMidiNote': '#000000', 
            'blackNoteDirection': 'v'
        }
        return defaults.get(field_name, None)
    
    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        return super().__getattribute__(field_name)
    
    def set_score_reference(self, score: 'SCORE'):
        """Set the score reference for inheritance."""
        object.__setattr__(self, 'score', score)
