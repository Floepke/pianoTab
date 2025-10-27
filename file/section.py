from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Section:
    id: int = 0
    time: float = 0.0
    text: str = 'Section'
    
    # looking to globalProperties for default values:
    color: str = '*'
    lineWidth: float = 0

    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalSection.color

    def lineWidth_(self, score: 'SCORE') -> float:
        '''Get the actual line width to use, considering inheritance.'''
        if self.lineWidth != 0:
            return self.lineWidth
        return score.properties.globalSection.lineWidth