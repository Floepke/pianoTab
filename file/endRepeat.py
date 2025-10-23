from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass
class EndRepeat:
    id: int = 0
    time: float = 0.0
    
    # looking to globalProperties for default values:
    color: str = '*'
    lineWidth: float = 0

    @property
    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalEndrepeat.color

    @property
    def lineWidth_(self, score: 'SCORE') -> float:
        '''Get the actual lineWidth to use, considering inheritance.'''
        if self.lineWidth != 0:
            return self.lineWidth
        return score.properties.globalEndrepeat.lineWidth