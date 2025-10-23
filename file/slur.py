from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

class Slur(BaseModel):
    '''
        A slur between two notes, represented as a cubic Bezier curve.

        some explenation of the control points:
        the x axis is pitch in semitones from C4. 
        for example if middle C = 40, -7 is f3 position, 6 = f#4 position
        So we use a grid in the x axis of semitones from C4
        the y axis is time in pianoticks (quarter note = 256.0)
    '''
    
    # Core fields
    id: int = Field(default=0)
    time: float = Field(default=0.0, description="Real field that appears in JSON")
    
    # Control points
    x1_semitonesFromC4: int = Field(default=0)
    x2_semitonesFromC4: int = Field(default=0)
    y2_time: float = Field(default=0.0)
    x3_semitonesFromC4: int = Field(default=0)
    y3_time: float = Field(default=0.0)
    x4_semitonesFromC4: int = Field(default=0)
    y4_time: float = Field(default=0.0)
    
    # Inheritable fields - None means inherit from global properties
    color: Optional[str] = Field(default=None, description="Color, None to inherit from globalSlur")
    startEndWidth: Optional[float] = Field(default=None, description="Start/end width, None to inherit from globalSlur")
    middleWidth: Optional[float] = Field(default=None, description="Middle width, None to inherit from globalSlur")
    
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
    
    @property
    def y1_time(self) -> float:
        '''Get the y1_time value (same as time).'''
        return self.time
    
    def __getattribute__(self, name: str):
        """Handle property inheritance transparently."""
        # Allow access to private/special attributes and methods
        if (name.startswith('_') or name in ('dict', 'json', 'copy', '__fields__', 'Config', 'score', 'y1_time') or
            hasattr(BaseModel, name)):
            return super().__getattribute__(name)
        
        # Get the stored value
        value = super().__getattribute__(name)
        
        # Check if this field should inherit (value is None)
        if value is None and name in ['color', 'startEndWidth', 'middleWidth']:
            return self._get_inherited_value(name)
        
        return value
    
    def _get_inherited_value(self, field_name: str):
        """Get the inherited value from global properties."""
        score = super().__getattribute__('score')
        if score is None:
            return self._get_default_value(field_name)
        
        if field_name == 'color':
            return score.properties.globalSlur.color
        elif field_name == 'startEndWidth':
            return score.properties.globalSlur.startEndWidth
        elif field_name == 'middleWidth':
            return score.properties.globalSlur.middleWidth
        
        return self._get_default_value(field_name)
    
    def _get_default_value(self, field_name: str):
        """Get default values when no score reference."""
        defaults = {
            'color': '#000000',
            'startEndWidth': 1.0,
            'middleWidth': 2.0
        }
        return defaults.get(field_name, None)
    
    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        return super().__getattribute__(field_name)
    
    def set_score_reference(self, score: 'SCORE'):
        """Set the score reference for inheritance."""
        object.__setattr__(self, 'score', score)
    
    def set_y1_time(self, value: float):
        """Set both y1_time and time to the same value."""
        object.__setattr__(self, 'time', value)