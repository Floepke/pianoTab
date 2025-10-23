from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass
class Countline:
    id: int = 0
    time: float = 0.0
    pitch1: int = 40
    pitch2: int = 44

    # looking to globalProperties for default values:
    color: str = '*'
    dashPattern: List[int] = field(default_factory=[2,2])

    @property
    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalCountLine.color
    
    @property
    def middleWidth_(self, score: 'SCORE') -> float:
        '''Get the actual width to use, considering inheritance.'''
        if self.middleWidth != 0:
            return self.middleWidth
        return score.properties.globalCountLine.middleWidth

    @property
    def dashPattern_(self, score: 'SCORE') -> List[int]:
        '''Get the actual dash pattern to use, considering inheritance.'''
        if self.dashPattern != [2, 2]:
            return self.dashPattern
        return score.properties.globalCountLine.dashPattern
