from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Slur:
    '''
        A slur between two notes, represented as a cubic Bezier curve.

        some explenation of the control points:
        the x axis is pitch in semitones from C4. 
        for example if middle C = 40, -7 is f3 position, 6 = f#4 position
        So we use a grid in the x axis of semitones from C4
        the y axis is time in pianoticks (quarter note = 256.0)
    '''
    id: int = 0
    time: float = 0.0  # Real field that appears in JSON
    
    # control points:
    x1_semitonesFromC4: int = field(default=0, metadata=config(field_name='x1'))
    x2_semitonesFromC4: int = field(default=0, metadata=config(field_name='x2'))
    y2_time: float = field(default=0.0, metadata=config(field_name='y2'))
    x3_semitonesFromC4: int = field(default=0, metadata=config(field_name='x3'))
    y3_time: float = field(default=0.0, metadata=config(field_name='y3'))
    x4_semitonesFromC4: int = field(default=0, metadata=config(field_name='x4'))
    y4_time: float = field(default=0.0, metadata=config(field_name='y4'))

    # Storage fields for inherited properties (serialize to JSON with clean names)
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    _startEndWidth: Optional[float] = field(default=None, metadata=config(field_name='seWid'))
    _middleWidth: Optional[float] = field(default=None, metadata=config(field_name='midWid'))

    def __post_init__(self):
        """Initialize score reference as a non-dataclass attribute."""
        self.score: Optional['SCORE'] = None
    
    @property
    def y1_time(self) -> float:
        '''Get the y1_time value (same as time).'''
        return self.time
    
    @y1_time.setter
    def y1_time(self, value: float):
        '''Set both y1_time and time to the same value.'''
        self.time = value
    
    # Property: color
    @property
    def color(self) -> str:
        """Get color - inherits from globalSlur.color if None."""
        if self._color is not None:
            return self._color
        if self.score is None:
            print("Warning: Slur has no score reference for property inheritance.")
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalSlur.color
    
    @color.setter
    def color(self, value: Optional[str]):
        """Set color - use None to reset to inheritance."""
        self._color = value
    
    # Property: startEndWidth
    @property
    def startEndWidth(self) -> float:
        """Get startEndWidth - inherits from globalSlur.startEndWidth if None."""
        if self._startEndWidth is not None:
            return self._startEndWidth
        if self.score is None:
            print("Warning: Slur has no score reference for property inheritance.")
            return 0.5  # Fallback if no score reference
        return self.score.properties.globalSlur.startEndWidth
    
    @startEndWidth.setter
    def startEndWidth(self, value: Optional[float]):
        """Set startEndWidth - use None to reset to inheritance."""
        self._startEndWidth = value
    
    # Property: middleWidth
    @property
    def middleWidth(self) -> float:
        """Get middleWidth - inherits from globalSlur.middleWidth if None."""
        if self._middleWidth is not None:
            return self._middleWidth
        if self.score is None:
            print("Warning: Slur has no score reference for property inheritance.")
            return 1.0  # Fallback if no score reference
        return self.score.properties.globalSlur.middleWidth
    
    @middleWidth.setter
    def middleWidth(self, value: Optional[float]):
        """Set middleWidth - use None to reset to inheritance."""
        self._middleWidth = value