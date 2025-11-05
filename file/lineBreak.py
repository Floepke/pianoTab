from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from typing import Literal, List
from file.staveRange import StaveRange

@dataclass_json
@dataclass
class LineBreak:
    '''
    Describes a line of music in the document.
    Each lineBreak contains staveRange objects - one per stave in the score.
    The staveRange list must always match the number of staves in the score.
    '''
    id: int = 0
    time: float = 0.0
    type: Literal['manual', 'locked'] = 'manual'  # manual = user defined, locked = cannot be removed and has time 0.0 is essential for the score.
    staveRange: List[StaveRange] = field(default_factory=list)
    
    def __post_init__(self):
        '''Ensure 'locked' type always has time=0.0'''
        if self.type == 'locked':
            object.__setattr__(self, 'time', 0.0)