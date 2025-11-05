from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import Literal, TYPE_CHECKING, Optional
if TYPE_CHECKING: 
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Text:
    id: int = 0
    time: float = 0.0 # time y position
    side: Literal['<', '>'] = '>'  # left or right of staff
    distFromSide: float = 10.0  # distance from side in mm
    text: str = 'Text'
    
    # Storage fields for inherited properties (serialize to JSON with clean names)
    _fontSize: Optional[int] = field(default=None, metadata=config(field_name='fontSize'))
    _color: Optional[str] = field(default=None, metadata=config(field_name='color'))
    
    def __post_init__(self):
        '''Initialize score reference as a non-dataclass attribute.'''
        self.score: Optional['SCORE'] = None
    
    # Property: fontSize
    @property
    def fontSize(self) -> int:
        '''Get fontSize - inherits from globalText.fontSize if None.'''
        if self._fontSize is not None:
            return self._fontSize
        if self.score is None:
            print('Warning: Text has no score reference for property inheritance.')
            return 12  # Fallback if no score reference
        return self.score.properties.globalText.fontSize
    
    @fontSize.setter
    def fontSize(self, value: Optional[int]):
        '''Set fontSize - use None to reset to inheritance.'''
        self._fontSize = value
    
    # Property: color
    @property
    def color(self) -> str:
        '''Get color - inherits from globalText.color if None.'''
        if self._color is not None:
            return self._color
        if self.score is None:
            print('Warning: Text has no score reference for property inheritance.')
            return '#000000'  # Fallback if no score reference
        return self.score.properties.globalText.color
    
    @color.setter
    def color(self, value: Optional[str]):
        '''Set color - use None to reset to inheritance.'''
        self._color = value
