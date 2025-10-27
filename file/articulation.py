from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import TYPE_CHECKING, Union, Literal
if TYPE_CHECKING:
    from file.SCORE import SCORE

@dataclass_json
@dataclass
class Articulation:
    # Core fields
    type: str = 'staccato'
    xOffset: float = 0.0
    yOffset: float = 0.0

    # looking to globalProperties for default values:
    color: Union[Literal['*'], str] = '*'  # '*' means inherit, otherwise a color string like '#RRGGBB'

    def get_color(self, score: 'SCORE') -> str:
        '''Get the actual color to use, considering inheritance.'''
        if self.color != '*':
            return self.color
        return score.properties.globalArticulation.color
