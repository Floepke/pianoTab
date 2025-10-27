from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class GraceNote:
    id: int = 0
    time: float = 0.0
    pitch: int = 60
    velocity: int = 80
    
    # looking to globalProperties for default values:
    color: str = '*'

    def color_(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalGraceNote.color