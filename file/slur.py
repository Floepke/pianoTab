from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import TYPE_CHECKING
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
    x1_semitonesFromC4: int = 0
    x2_semitonesFromC4: int = 0
    y2_time: float = 0.0
    x3_semitonesFromC4: int = 0
    y3_time: float = 0.0
    x4_semitonesFromC4: int = 0
    y4_time: float = 0.0

    # looking to globalProperties for default values:
    color: str = '*'
    startEndWidth: float = 0
    middleWidth: float = 0

    def __post_init__(self):
        """Ensure time and y1_time stay synchronized after initialization."""
        # If time was set during init, sync y1_time
        self._sync_y1_time_to_time()
    
    def _sync_y1_time_to_time(self):
        """Internal method to sync y1_time with time."""
        # This is called when time changes
        pass  # y1_time is handled by the property
    
    @property
    def y1_time(self) -> float:
        '''Get the y1_time value (same as time).'''
        return self.time
    
    @y1_time.setter
    def y1_time(self, value: float):
        '''Set both y1_time and time to the same value.'''
        self.time = value

    @property
    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalSlur.color
    
    @property
    def startEndWidth_(self, score: 'SCORE') -> float:
        '''Get the actual startEndWidth to use, considering inheritance.'''
        if self.startEndWidth != 0:
            return self.startEndWidth
        return score.properties.globalSlur.startEndWidth

    @property
    def middleWidth_(self, score: 'SCORE') -> float:
        '''Get the actual middleWidth to use, considering inheritance.'''
        if self.middleWidth != 0:
            return self.middleWidth
        return score.properties.globalSlur.middleWidth