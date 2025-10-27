from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Beam:
    id: int = 0
    time: float = 0.0
    staff: float = 0.0
    hand: Literal['<', '>'] = '<'
    
    # looking to globalProperties for default values:
    color: str = '*'
    width: float = 0
    slant: float = 0

    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalBeam.color

    def width_(self, score: 'SCORE') -> float:
        '''Get the actual width to use, considering inheritance.'''
        if self.width != 0:
            return self.width
        return score.properties.globalBeam.width

    def slant_(self, score: 'SCORE') -> float:
        '''Get the actual slant to use, considering inheritance.'''
        if self.slant != 0:
            return self.slant
        return score.properties.globalBeam.slant