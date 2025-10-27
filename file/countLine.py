from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class CountLine:
    id: int = 0
    time: float = 0.0
    pitch1: int = 40
    pitch2: int = 44

    # looking to globalProperties for default values:
    color: str = '*'
    dashPattern: List[int] = field(default_factory=lambda: [2,2])

    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalCountLine.color

    def dashPattern_(self, score: 'SCORE') -> List[int]:
        '''Get the actual dash pattern to use, considering inheritance.'''
        if self.dashPattern != [2, 2]:
            return self.dashPattern
        return score.properties.globalCountLine.dashPattern
