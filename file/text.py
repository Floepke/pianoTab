from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING: 
    from file import SCORE

@dataclass
class Text:
    id: int = 0
    time: float = 0.0 # time y position
    side: Literal['<', '>'] = '>'  # left or right of staff
    distFromSide: float = 10.0  # distance from side in mm
    text: str = 'Text'
    
    # looking to globalProperties for default values:
    fontSize: int = 0
    color: str = '*' # '*' means inherit, otherwise a color string like '#RRGGBB'

    @property
    def fontSize_(self, score: 'SCORE') -> int:
        '''Get the actual font size to use, considering inheritance.'''
        if self.fontSize != 0:
            return self.fontSize
        return score.properties.globalText.fontSize

    @property
    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalText.color
