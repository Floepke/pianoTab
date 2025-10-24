from pydantic import BaseModel, Field
from typing import TYPE_CHECKING, Optional
from file.inherit_field import InheritMixin
if TYPE_CHECKING:
    from file.SCORE import SCORE

class Slur(InheritMixin, BaseModel):
    _INHERIT_CONFIG = {
        'color': ('_color', 'properties.globalSlur.color', '#000000'),
        'startEndWidth': ('_startEndWidth', 'properties.globalSlur.startEndWidth', 1.0),
        'middleWidth': ('_middleWidth', 'properties.globalSlur.middleWidth', 2.0),
    }
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
    # y1_time seems missing but we use the time field both as y1_time and time
    x2_semitonesFromC4: int = Field(default=0)
    y2_time: float = Field(default=0.0)
    x3_semitonesFromC4: int = Field(default=0)
    y3_time: float = Field(default=0.0)
    x4_semitonesFromC4: int = Field(default=0)
    y4_time: float = Field(default=0.0)
    
    # Private storage for inheritable fields
    _color: Optional[str] = Field(default=None, alias='color', description="Color, None to inherit from globalSlur")
    _startEndWidth: Optional[float] = Field(default=None, alias='startEndWidth', description="Start/end width, None to inherit from globalSlur")
    _middleWidth: Optional[float] = Field(default=None, alias='middleWidth', description="Middle width, None to inherit from globalSlur")
    
    # Score reference (not serialized to JSON)
    score: Optional['SCORE'] = Field(default=None, exclude=True)
    
    class Config:
        extra = 'ignore'
        use_enum_values = True
        arbitrary_types_allowed = True
        populate_by_name = True
    
    def __init__(self, **data):
        # Extract score reference to set after initialization
        score = data.pop('score', None)
        super().__init__(**data)
        if score is not None:
            self.set_score_reference(score)
    
    @property
    def y1_time(self) -> float:
        '''Get the y1_time value (same as time).'''
        return self.time
    

    def get_literal_value(self, field_name: str):
        """Get the actual stored value without inheritance."""
        private_name = f'_{field_name}' if not field_name.startswith('_') else field_name
        return getattr(self, private_name, None)
    
    def set_y1_time(self, value: float):
        """Set both y1_time and time to the same value."""
        object.__setattr__(self, 'time', value)
